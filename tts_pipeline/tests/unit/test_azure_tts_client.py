"""
Unit tests for Azure TTS Client

Tests the AzureTTSClient functionality including configuration loading,
SSML generation, API integration, and error handling.
"""

import os
import json
import sys
import pytest
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.azure_tts_client import AzureTTSClient
from utils.project_manager import Project


class TestAzureTTSClient:
    """Test cases for AzureTTSClient class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Azure configuration."""
        return {
            "voice_name": "en-US-SteffanNeural",
            "output_format": "audio-24khz-160kbitrate-mono-mp3",
            "rate": "+0%",
            "pitch": "+0Hz",
            "max_text_length": 5000,
            "timeout_seconds": 300,
            "language": "en-US",
            "voice_gender": "male"
        }
    
    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-subscription-key',
            'AZURE_TTS_REGION': 'eastus'
        }, clear=True):
            yield
    
    @pytest.fixture
    def mock_env_vars_with_endpoint(self):
        """Mock environment variables with custom endpoint."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-subscription-key',
            'AZURE_ENDPOINT': 'https://my-custom-endpoint.cognitiveservices.azure.com'
        }, clear=True):
            yield
    
    @pytest.fixture
    def azure_client(self, temp_config_file, mock_env_vars):
        """Create AzureTTSClient instance for testing."""
        return AzureTTSClient(project_or_config_path=temp_config_file)
    
    def test_init_success(self, temp_config_file, mock_env_vars):
        """Test successful AzureTTSClient initialization."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        assert client.subscription_key == 'test-subscription-key'
        assert client.region == 'eastus'
        assert client.config['voice_name'] == 'en-US-SteffanNeural'
        assert client.synthesis_url == 'https://eastus.tts.speech.microsoft.com/cognitiveservices/v1'
    
    def test_init_missing_subscription_key(self, temp_config_file):
        """Test initialization fails without subscription key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AZURE_TTS_SUBSCRIPTION_KEY environment variable is required"):
                AzureTTSClient(project_or_config_path=temp_config_file)
    
    def test_init_default_region(self, temp_config_file):
        """Test initialization with default region."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key'
        }, clear=True):
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            assert client.region == 'westus'
    
    def test_init_custom_region(self, temp_config_file):
        """Test initialization with custom region."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_TTS_REGION': 'westus2'
        }, clear=True):
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            assert client.region == 'westus2'
            assert 'westus2' in client.synthesis_url
    
    def test_init_custom_endpoint(self, temp_config_file):
        """Test initialization with custom endpoint."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_ENDPOINT': 'https://my-custom-endpoint.cognitiveservices.azure.com'
        }, clear=True):
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            assert client.endpoint == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert client.base_url == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert client.synthesis_url == 'https://my-custom-endpoint.cognitiveservices.azure.com/cognitiveservices/v1'
    
    def test_init_custom_endpoint_with_trailing_slash(self, temp_config_file):
        """Test initialization with custom endpoint that has trailing slash."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_ENDPOINT': 'https://my-custom-endpoint.cognitiveservices.azure.com/'
        }, clear=True):
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            assert client.base_url == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert client.synthesis_url == 'https://my-custom-endpoint.cognitiveservices.azure.com/cognitiveservices/v1'
    
    def test_load_config_success(self, temp_config_file, mock_env_vars):
        """Test successful config loading."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        assert client.config['voice_name'] == 'en-US-SteffanNeural'
        assert client.config['language'] == 'en-US'
    
    def test_load_config_file_not_found(self, mock_env_vars):
        """Test config loading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            AzureTTSClient(project_or_config_path='nonexistent.json')
    
    def test_load_config_invalid_json(self, mock_env_vars):
        """Test config loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                AzureTTSClient(project_or_config_path=temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_create_ssml_basic(self, azure_client):
        """Test SSML creation with basic text."""
        text = "Hello world"
        ssml = azure_client._create_ssml(text)
        
        assert 'en-US-SteffanNeural' in ssml
        assert 'Hello world' in ssml
        assert '<speak version=\'1.0\'' in ssml
        assert '<voice name=' in ssml
        assert '<prosody rate=\'+0%\' pitch=\'+0Hz\'>' in ssml
    
    def test_create_ssml_xml_escaping(self, azure_client):
        """Test SSML creation with XML special characters."""
        text = "Test & < > characters"
        ssml = azure_client._create_ssml(text)
        
        assert '&amp;' in ssml
        assert '&lt;' in ssml
        assert '&gt;' in ssml
        assert 'Test &amp; &lt; &gt; characters' in ssml
    
    def test_create_ssml_empty_text(self, azure_client):
        """Test SSML creation with empty text."""
        ssml = azure_client._create_ssml("")
        
        assert 'en-US-SteffanNeural' in ssml
        assert '<prosody rate=\'+0%\' pitch=\'+0Hz\'>' in ssml
        assert '</prosody>' in ssml
    
    @patch('requests.post')
    def test_synthesize_text_success(self, mock_post, azure_client):
        """Test successful text synthesis."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake audio content'
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name
        
        try:
            result = azure_client.synthesize_text("Hello world", output_path)
            
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == azure_client.synthesis_url
            assert call_args[1]['headers'] == azure_client.headers
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('requests.post')
    def test_synthesize_text_api_error(self, mock_post, azure_client):
        """Test text synthesis with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        result = azure_client.synthesize_text("Hello world", "/tmp/test.mp3")
        
        assert result is False
    
    @patch('requests.post')
    def test_synthesize_text_timeout(self, mock_post, azure_client):
        """Test text synthesis with timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = azure_client.synthesize_text("Hello world", "/tmp/test.mp3")
        
        assert result is False
    
    @patch('requests.post')
    def test_synthesize_text_request_exception(self, mock_post, azure_client):
        """Test text synthesis with request exception."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result = azure_client.synthesize_text("Hello world", "/tmp/test.mp3")
        
        assert result is False
    
    def test_synthesize_text_too_long(self, azure_client):
        """Test text synthesis with text exceeding max length."""
        long_text = "x" * (azure_client.config['max_text_length'] + 1)
        
        result = azure_client.synthesize_text(long_text, "/tmp/test.mp3")
        
        assert result is False
    
    def test_synthesize_text_creates_directory(self, azure_client):
        """Test that synthesize_text creates output directory."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'fake audio content'
            mock_post.return_value = mock_response
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'subdir', 'test.mp3')
                
                result = azure_client.synthesize_text("Hello world", output_path)
                
                assert result is True
                assert os.path.exists(output_path)
                assert os.path.exists(os.path.dirname(output_path))
    
    def test_get_voice_info(self, temp_config_file, mock_env_vars):
        """Test getting voice information."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        voice_info = client.get_voice_info()
        
        assert voice_info['voice_name'] == 'en-US-SteffanNeural'
        assert voice_info['language'] == 'en-US'
        assert voice_info['gender'] == 'male'
        assert voice_info['output_format'] == 'audio-24khz-160kbitrate-mono-mp3'
        assert voice_info['region'] == 'eastus'
        assert voice_info['endpoint'] is None  # No custom endpoint set
        assert 'eastus' in voice_info['base_url']
    
    def test_get_voice_info_with_endpoint(self, temp_config_file):
        """Test getting voice information with custom endpoint."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_ENDPOINT': 'https://my-custom-endpoint.cognitiveservices.azure.com'
        }):
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            voice_info = client.get_voice_info()
            
            assert voice_info['voice_name'] == 'en-US-SteffanNeural'
            assert voice_info['language'] == 'en-US'
            assert voice_info['gender'] == 'male'
            assert voice_info['output_format'] == 'audio-24khz-160kbitrate-mono-mp3'
            assert voice_info['endpoint'] == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert voice_info['base_url'] == 'https://my-custom-endpoint.cognitiveservices.azure.com'
    
    @patch('requests.post')
    def test_test_connection_success(self, mock_post, azure_client):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = azure_client.test_connection()
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_test_connection_failure(self, mock_post, azure_client):
        """Test connection test failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        result = azure_client.test_connection()
        
        assert result is False
    
    @patch('requests.post')
    def test_test_connection_exception(self, mock_post, azure_client):
        """Test connection test with exception."""
        mock_post.side_effect = Exception("Connection error")
        
        result = azure_client.test_connection()
        
        assert result is False
    
    def test_default_config_path(self, mock_env_vars):
        """Test that default config path is used when none provided."""
        # Create a temporary config file in the expected location
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_file = config_dir / "azure_config.json"
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup original if it exists
        original_exists = config_file.exists()
        if original_exists:
            backup_content = config_file.read_text()
        
        try:
            # Create test config
            test_config = {
                "voice_name": "en-US-SteffanNeural",
                "output_format": "audio-24khz-160kbitrate-mono-mp3",
                "rate": "+0%",
                "pitch": "+0Hz",
                "max_text_length": 5000,
                "timeout_seconds": 300,
                "language": "en-US",
                "voice_gender": "male"
            }
            config_file.write_text(json.dumps(test_config))
            
            # Test with no config path
            client = AzureTTSClient(project_or_config_path=None)
            assert client.config['voice_name'] == 'en-US-SteffanNeural'
            
        finally:
            # Restore original config
            if original_exists:
                config_file.write_text(backup_content)
            elif config_file.exists():
                config_file.unlink()


class TestAzureTTSClientIntegration:
    """Integration tests for AzureTTSClient."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Azure configuration for integration tests."""
        return {
            "voice_name": "en-US-SteffanNeural",
            "output_format": "audio-24khz-160kbitrate-mono-mp3",
            "rate": "+0%",
            "pitch": "+0Hz",
            "max_text_length": 5000,
            "timeout_seconds": 300,
            "language": "en-US",
            "voice_gender": "male"
        }
    
    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create temporary config file for integration testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for integration tests."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-subscription-key',
            'AZURE_TTS_REGION': 'eastus'
        }):
            yield
    
    def test_full_workflow_simulation(self, temp_config_file, mock_env_vars):
        """Test complete workflow simulation with mocked API."""
        with patch('requests.post') as mock_post:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'fake audio content'
            mock_post.return_value = mock_response
            
            # Create client
            client = AzureTTSClient(project_or_config_path=temp_config_file)
            
            # Test connection
            assert client.test_connection() is True
            
            # Get voice info
            voice_info = client.get_voice_info()
            assert voice_info['voice_name'] == 'en-US-SteffanNeural'
            
            # Synthesize text
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                output_path = f.name
            
            try:
                result = client.synthesize_text("Hello, this is a test.", output_path)
                assert result is True
                assert os.path.exists(output_path)
                
                # Verify file content
                with open(output_path, 'rb') as f:
                    content = f.read()
                assert content == b'fake audio content'
                
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
    
    def test_error_recovery_scenarios(self, temp_config_file, mock_env_vars):
        """Test various error recovery scenarios."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        # Test with various error conditions
        test_cases = [
            ("Text too long", "x" * 6000, False),
            ("Empty text", "", True),  # Empty text should work
            ("Special characters", "Test & < > \" ' characters", True),
        ]
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'fake audio content'
            mock_post.return_value = mock_response
            
            for description, text, expected_success in test_cases:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    output_path = f.name
                
                try:
                    result = client.synthesize_text(text, output_path)
                    if expected_success:
                        assert result is True, f"Failed for: {description}"
                    else:
                        assert result is False, f"Should have failed for: {description}"
                        
                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)


class TestAzureTTSClientProjectBased:
    """Test cases for AzureTTSClient with project-based configuration."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Azure configuration."""
        return {
            "voice_name": "en-US-SteffanNeural",
            "output_format": "audio-24khz-160kbitrate-mono-mp3",
            "rate": "+0%",
            "pitch": "+0Hz",
            "max_text_length": 5000,
            "timeout_seconds": 300,
            "language": "en-US",
            "voice_gender": "male"
        }
    
    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def mock_project(self):
        """Create a mock Project object for testing."""
        project = Mock(spec=Project)
        project.project_name = "test_project"
        project.project_config = {
            'display_name': 'Test Project',
            'metadata': {'total_chapters': 100}
        }
        project.get_azure_config.return_value = {
            "voice_name": "en-US-SteffanNeural",
            "output_format": "audio-24khz-160kbitrate-mono-mp3",
            "rate": "+0%",
            "pitch": "+0Hz",
            "max_text_length": 20000,
            "timeout_seconds": 1200,
            "language": "en-US",
            "voice_gender": "male"
        }
        return project
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-subscription-key',
            'AZURE_TTS_REGION': 'eastus',
            'AZURE_ENDPOINT': ''  # Clear any existing endpoint
        }, clear=True):
            yield
    
    def test_init_with_project(self, mock_project, mock_env_vars):
        """Test initialization with Project object."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        assert client.subscription_key == 'test-subscription-key'
        assert client.region == 'eastus'
        assert client.config['voice_name'] == 'en-US-SteffanNeural'
        assert client.config['max_text_length'] == 20000
        assert client.config['timeout_seconds'] == 1200
        assert hasattr(client, 'project')
        assert client.project == mock_project
        assert client.is_project_based() is True
        assert client.get_configuration_source() == 'project'
    
    def test_init_with_project_custom_endpoint(self, mock_project):
        """Test initialization with Project object and custom endpoint."""
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_ENDPOINT': 'https://my-custom-endpoint.cognitiveservices.azure.com'
        }):
            client = AzureTTSClient(project_or_config_path=mock_project)
            
            assert client.endpoint == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert client.base_url == 'https://my-custom-endpoint.cognitiveservices.azure.com'
            assert client.synthesis_url == 'https://my-custom-endpoint.cognitiveservices.azure.com/cognitiveservices/v1'
    
    def test_get_project_name(self, mock_project, mock_env_vars):
        """Test getting project name."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        assert client.get_project_name() == 'test_project'
    
    def test_get_project_name_file_based(self, temp_config_file, mock_env_vars):
        """Test getting project name with file-based config."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        assert client.get_project_name() is None
    
    def test_is_project_based(self, mock_project, mock_env_vars):
        """Test project-based detection."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        assert client.is_project_based() is True
    
    def test_is_project_based_file_config(self, temp_config_file, mock_env_vars):
        """Test project-based detection with file config."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        assert client.is_project_based() is False
    
    def test_get_configuration_source(self, mock_project, mock_env_vars):
        """Test configuration source detection."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        assert client.get_configuration_source() == 'project'
    
    def test_get_configuration_source_file(self, temp_config_file, mock_env_vars):
        """Test configuration source detection with file config."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        assert client.get_configuration_source() == 'file'
    
    def test_get_voice_info_with_project(self, mock_project, mock_env_vars):
        """Test getting voice information with project-based config."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        voice_info = client.get_voice_info()
        
        assert voice_info['voice_name'] == 'en-US-SteffanNeural'
        assert voice_info['language'] == 'en-US'
        assert voice_info['gender'] == 'male'
        assert voice_info['max_text_length'] == 20000
        assert voice_info['timeout_seconds'] == 1200
        assert voice_info['project_name'] == 'test_project'
        assert voice_info['project_display_name'] == 'Test Project'
        assert voice_info['configuration_source'] == 'project'
    
    def test_get_voice_info_file_based(self, temp_config_file, mock_env_vars):
        """Test getting voice information with file-based config."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        voice_info = client.get_voice_info()
        
        assert voice_info['voice_name'] == 'en-US-SteffanNeural'
        assert voice_info['language'] == 'en-US'
        assert voice_info['gender'] == 'male'
        assert voice_info['max_text_length'] == 5000
        assert voice_info['timeout_seconds'] == 300
        assert 'project_name' not in voice_info
        assert voice_info['configuration_source'] == 'file'
    
    @patch('requests.post')
    def test_synthesize_text_with_project(self, mock_post, mock_project, mock_env_vars):
        """Test text synthesis with project-based config."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'fake audio content'
        mock_post.return_value = mock_response
        
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name
        
        try:
            result = client.synthesize_text("Hello world", output_path)
            
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == client.synthesis_url
            assert call_args[1]['headers'] == client.headers
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_synthesize_text_too_long_project_config(self, mock_project, mock_env_vars):
        """Test text synthesis with text exceeding project's max length."""
        client = AzureTTSClient(project_or_config_path=mock_project)
        long_text = "x" * (client.config['max_text_length'] + 1)
        
        result = client.synthesize_text(long_text, "/tmp/test.mp3")
        
        assert result is False
    
    @patch('requests.post')
    def test_test_connection_with_project(self, mock_post, mock_project, mock_env_vars):
        """Test connection test with project-based config."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = AzureTTSClient(project_or_config_path=mock_project)
        
        result = client.test_connection()
        
        assert result is True
        mock_post.assert_called_once()
    
    def test_backward_compatibility_none_param(self, mock_env_vars):
        """Test backward compatibility with None parameter."""
        # Create a temporary config file in the expected location
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_file = config_dir / "azure_config.json"
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup original if it exists
        original_exists = config_file.exists()
        if original_exists:
            backup_content = config_file.read_text()
        
        try:
            # Create test config
            test_config = {
                "voice_name": "en-US-SteffanNeural",
                "output_format": "audio-24khz-160kbitrate-mono-mp3",
                "rate": "+0%",
                "pitch": "+0Hz",
                "max_text_length": 5000,
                "timeout_seconds": 300,
                "language": "en-US",
                "voice_gender": "male"
            }
            config_file.write_text(json.dumps(test_config))
            
            # Test with None parameter (should use default config path)
            client = AzureTTSClient(project_or_config_path=None)
            assert client.config['voice_name'] == 'en-US-SteffanNeural'
            assert client.is_project_based() is False
            assert client.get_configuration_source() == 'file'
            
        finally:
            # Restore original config
            if original_exists:
                config_file.write_text(backup_content)
            elif config_file.exists():
                config_file.unlink()
    
    def test_backward_compatibility_string_param(self, temp_config_file, mock_env_vars):
        """Test backward compatibility with string parameter."""
        client = AzureTTSClient(project_or_config_path=temp_config_file)
        
        assert client.config['voice_name'] == 'en-US-SteffanNeural'
        assert client.is_project_based() is False
        assert client.get_configuration_source() == 'file'
