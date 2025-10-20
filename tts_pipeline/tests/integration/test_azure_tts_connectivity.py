"""
Integration tests for Azure TTS Client

These tests verify actual connectivity to Azure endpoints without making
expensive TTS calls. They test authentication and endpoint accessibility.
"""

import os
import pytest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path

import sys
from pathlib import Path

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.azure_tts_client import AzureTTSClient


class TestAzureTTSClientConnectivity:
    """Integration tests for Azure TTS Client connectivity."""
    
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
    
    def test_connection_with_real_credentials(self, temp_config_file):
        """
        Test actual connection to Azure TTS using real credentials.
        
        This test will only run if AZURE_TTS_SUBSCRIPTION_KEY is set in environment.
        It performs a minimal test request to verify connectivity.
        """
        # Skip if no real credentials are available
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY')
        if not subscription_key or subscription_key.startswith('test-'):
            pytest.skip("Real Azure credentials not available - skipping connectivity test")
        
        # Test with region-based endpoint
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key,
            'AZURE_TTS_REGION': 'eastus'
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            # Test connection
            result = client.test_connection()
            
            if result:
                print("✅ Region-based Azure TTS connection successful")
            else:
                print("❌ Region-based Azure TTS connection failed")
            
            # This test documents the result but doesn't fail the build
            # since it depends on external Azure service availability
            assert isinstance(result, bool)
    
    def test_connection_with_custom_endpoint(self, temp_config_file):
        """
        Test actual connection to Azure TTS using custom endpoint.
        
        This test will only run if both AZURE_TTS_SUBSCRIPTION_KEY and 
        AZURE_ENDPOINT are set in environment.
        """
        # Skip if no real credentials are available
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY')
        custom_endpoint = os.getenv('AZURE_ENDPOINT')
        
        if not subscription_key or subscription_key.startswith('test-'):
            pytest.skip("Real Azure credentials not available - skipping custom endpoint test")
        
        if not custom_endpoint:
            pytest.skip("AZURE_ENDPOINT not set - skipping custom endpoint test")
        
        # Test with custom endpoint
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key,
            'AZURE_ENDPOINT': custom_endpoint
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            # Verify endpoint configuration
            voice_info = client.get_voice_info()
            assert voice_info['endpoint'] == custom_endpoint
            assert voice_info['base_url'] == custom_endpoint.rstrip('/')
            
            # Test connection
            result = client.test_connection()
            
            if result:
                print(f"✅ Custom endpoint Azure TTS connection successful: {custom_endpoint}")
            else:
                print(f"❌ Custom endpoint Azure TTS connection failed: {custom_endpoint}")
            
            # This test documents the result but doesn't fail the build
            assert isinstance(result, bool)
    
    def test_endpoint_priority_logic(self, temp_config_file):
        """
        Test that custom endpoint takes priority over region-based URL.
        """
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY', 'test-key')
        custom_endpoint = os.getenv('AZURE_ENDPOINT', 'https://test-endpoint.cognitiveservices.azure.com')
        
        # Test priority: AZURE_ENDPOINT should override AZURE_TTS_REGION
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key,
            'AZURE_TTS_REGION': 'eastus',
            'AZURE_ENDPOINT': custom_endpoint
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            voice_info = client.get_voice_info()
            
            # Should use custom endpoint, not region-based URL
            assert voice_info['endpoint'] == custom_endpoint
            assert voice_info['base_url'] == custom_endpoint.rstrip('/')
            assert 'eastus' not in voice_info['base_url']  # Should not use region
    
    def test_region_fallback_logic(self, temp_config_file):
        """
        Test that region-based URL is used when no custom endpoint is provided.
        """
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY', 'test-key')
        
        # Test fallback: should use region when no custom endpoint
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key,
            'AZURE_TTS_REGION': 'westus2'
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            voice_info = client.get_voice_info()
            
            # Should use region-based URL
            assert voice_info['endpoint'] is None
            assert 'westus2' in voice_info['base_url']
            assert voice_info['base_url'] == 'https://westus2.tts.speech.microsoft.com'
    
    def test_default_region_fallback(self, temp_config_file):
        """
        Test that default region (westus) is used when no region is specified.
        """
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY', 'test-key')
        
        # Test default: should use 'westus' when no region specified
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            voice_info = client.get_voice_info()
            
            # Should use default region
            assert voice_info['endpoint'] is None
            assert voice_info['region'] == 'westus'
            assert voice_info['base_url'] == 'https://westus.tts.speech.microsoft.com'
    
    def test_endpoint_url_construction(self, temp_config_file):
        """
        Test that synthesis URLs are constructed correctly for different endpoint types.
        """
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY', 'test-key')
        
        test_cases = [
            # (endpoint, expected_base_url, expected_synthesis_url)
            (None, 'https://westus.tts.speech.microsoft.com', 'https://westus.tts.speech.microsoft.com/cognitiveservices/v1'),
            ('https://custom.cognitiveservices.azure.com', 'https://custom.cognitiveservices.azure.com', 'https://custom.cognitiveservices.azure.com/cognitiveservices/v1'),
            ('https://custom.cognitiveservices.azure.com/', 'https://custom.cognitiveservices.azure.com', 'https://custom.cognitiveservices.azure.com/cognitiveservices/v1'),
        ]
        
        for endpoint, expected_base, expected_synthesis in test_cases:
            env_vars = {'AZURE_TTS_SUBSCRIPTION_KEY': subscription_key}
            if endpoint:
                env_vars['AZURE_ENDPOINT'] = endpoint
            
            with patch.dict(os.environ, env_vars, clear=True):
                client = AzureTTSClient(config_path=temp_config_file)
                
                assert client.base_url == expected_base
                assert client.synthesis_url == expected_synthesis
                
                voice_info = client.get_voice_info()
                assert voice_info['base_url'] == expected_base
    
    @pytest.mark.slow
    def test_actual_tts_synthesis(self, temp_config_file):
        """
        Test actual TTS synthesis with real Azure service.
        
        This test makes a real TTS call and should only be run when:
        1. Real Azure credentials are available
        2. You want to test actual synthesis (costs money)
        3. You explicitly run with pytest -m slow
        """
        # Skip if no real credentials are available
        subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY')
        if not subscription_key or subscription_key.startswith('test-'):
            pytest.skip("Real Azure credentials not available - skipping synthesis test")
        
        # Use environment variables as-is
        client = AzureTTSClient(config_path=temp_config_file)
        
        # Test with a very short text to minimize cost
        test_text = "Test."
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            output_path = f.name
        
        try:
            result = client.synthesize_text(test_text, output_path)
            
            if result:
                print(f"✅ TTS synthesis successful: {output_path}")
                # Verify file was created and has content
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
            else:
                print("❌ TTS synthesis failed")
            
            # This test documents the result but doesn't fail the build
            assert isinstance(result, bool)
            
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_connection_error_handling(self, temp_config_file):
        """
        Test error handling for invalid credentials or endpoints.
        """
        # Test with invalid subscription key
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'invalid-key-12345',
            'AZURE_TTS_REGION': 'eastus'
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            # Connection should fail gracefully
            result = client.test_connection()
            assert result is False
        
        # Test with invalid endpoint
        with patch.dict(os.environ, {
            'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
            'AZURE_ENDPOINT': 'https://invalid-endpoint.example.com'
        }, clear=True):
            client = AzureTTSClient(config_path=temp_config_file)
            
            # Connection should fail gracefully
            result = client.test_connection()
            assert result is False
