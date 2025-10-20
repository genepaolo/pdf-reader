"""
Azure Cognitive Services Text-to-Speech Client

This module provides a client for Azure Cognitive Services TTS API,
handling authentication, voice configuration, and audio generation.

Supports both project-based and file-based configuration:
- Project-based: Pass a Project object to use project-specific Azure settings
- File-based: Pass a config file path or use default path for backward compatibility
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path


class AzureTTSClient:
    """
    Azure Cognitive Services Text-to-Speech client.
    
    Handles authentication via environment variables, voice configuration,
    and audio generation with proper error handling.
    
    Supports both project-based and file-based configuration:
    - Project-based: Initialize with Project object for project-specific settings
    - File-based: Initialize with config file path for backward compatibility
    """
    
    def __init__(self, project_or_config_path=None):
        """
        Initialize Azure TTS client.
        
        Args:
            project_or_config_path: Either a Project object or path to azure_config.json file.
                                  If None, uses default path for backward compatibility.
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine if we're using project-based or file-based configuration
        if project_or_config_path is None:
            # Backward compatibility: use default config path
            config_path = Path(__file__).parent.parent / "config" / "azure_config.json"
            self.config = self._load_config(config_path)
            self.logger.info("Using legacy file-based Azure configuration")
        elif hasattr(project_or_config_path, 'get_azure_config'):
            # Project-based configuration
            self.project = project_or_config_path
            self.config = self.project.get_azure_config()
            self.logger.info(f"Using project-based Azure configuration for: {self.project.project_name}")
        else:
            # File-based configuration (backward compatibility)
            config_path = project_or_config_path
            self.config = self._load_config(config_path)
            self.logger.info(f"Using file-based Azure configuration from: {config_path}")
        
        # Get Azure credentials from environment variables
        self.subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY')
        self.region = os.getenv('AZURE_TTS_REGION', 'westus')
        self.endpoint = os.getenv('AZURE_ENDPOINT')
        
        if not self.subscription_key:
            raise ValueError(
                "AZURE_TTS_SUBSCRIPTION_KEY environment variable is required. "
                "Please set it with your Azure Cognitive Services subscription key."
            )
        
        # Azure TTS API endpoint - use custom endpoint if provided, otherwise use region-based URL
        if self.endpoint:
            # Use custom endpoint (remove trailing slash if present)
            self.base_url = self.endpoint.rstrip('/')
            self.synthesis_url = f"{self.base_url}/cognitiveservices/v1"
            self.logger.info(f"Using custom Azure endpoint: {self.base_url}")
        else:
            # Use region-based URL
            self.base_url = f"https://{self.region}.tts.speech.microsoft.com"
            self.synthesis_url = f"{self.base_url}/cognitiveservices/v1"
            self.logger.info(f"Using region-based Azure endpoint: {self.base_url}")
        
        # Request headers
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': self.config['output_format']
        }
        
        self.logger.info(f"Azure TTS client initialized for region: {self.region}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load Azure TTS configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.debug(f"Loaded Azure config from: {config_path}")
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Azure config file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Azure config file: {e}")
    
    def _create_ssml(self, text: str) -> str:
        """
        Create SSML (Speech Synthesis Markup Language) for the given text.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            SSML string formatted for Azure TTS
        """
        # Escape XML special characters
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{self.config['language']}'>
    <voice name='{self.config['voice_name']}'>
        <prosody rate='{self.config['rate']}' pitch='{self.config['pitch']}'>
            {escaped_text}
        </prosody>
    </voice>
</speak>"""
        
        return ssml
    
    def synthesize_text(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech and save as audio file.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate text length
            if len(text) > self.config['max_text_length']:
                self.logger.error(f"Text too long: {len(text)} chars (max: {self.config['max_text_length']})")
                return False
            
            # Create SSML
            ssml = self._create_ssml(text)
            
            # Make API request
            response = requests.post(
                self.synthesis_url,
                headers=self.headers,
                data=ssml.encode('utf-8'),
                timeout=self.config['timeout_seconds']
            )
            
            # Check response
            if response.status_code == 200:
                # Save audio file
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                self.logger.info(f"Successfully generated audio: {output_path}")
                return True
            else:
                self.logger.error(f"TTS API error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"TTS API timeout after {self.config['timeout_seconds']} seconds")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"TTS API request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during TTS synthesis: {e}")
            return False
    
    def get_voice_info(self) -> Dict[str, Any]:
        """
        Get current voice configuration information.
        
        Returns:
            Dictionary with voice configuration details
        """
        voice_info = {
            'voice_name': self.config['voice_name'],
            'language': self.config['language'],
            'gender': self.config['voice_gender'],
            'output_format': self.config['output_format'],
            'rate': self.config['rate'],
            'pitch': self.config['pitch'],
            'max_text_length': self.config['max_text_length'],
            'timeout_seconds': self.config['timeout_seconds'],
            'region': self.region,
            'endpoint': self.endpoint,
            'base_url': self.base_url
        }
        
        # Add project information if available
        if hasattr(self, 'project'):
            voice_info['project_name'] = self.project.project_name
            voice_info['project_display_name'] = self.project.project_config.get('display_name', 'N/A')
            voice_info['configuration_source'] = 'project'
        else:
            voice_info['configuration_source'] = 'file'
        
        return voice_info
    
    def get_project_name(self) -> Optional[str]:
        """
        Get the project name if using project-based configuration.
        
        Returns:
            Project name if available, None otherwise
        """
        return getattr(self.project, 'project_name', None) if hasattr(self, 'project') else None
    
    def is_project_based(self) -> bool:
        """
        Check if this client is using project-based configuration.
        
        Returns:
            True if using project-based config, False if using file-based config
        """
        return hasattr(self, 'project')
    
    def get_configuration_source(self) -> str:
        """
        Get the source of the configuration.
        
        Returns:
            'project' if using project-based config, 'file' if using file-based config
        """
        return 'project' if self.is_project_based() else 'file'
    
    def test_connection(self) -> bool:
        """
        Test Azure TTS API connection with a simple request.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_text = "Hello, this is a test of the Azure TTS connection."
            test_ssml = self._create_ssml(test_text)
            
            response = requests.post(
                self.synthesis_url,
                headers=self.headers,
                data=test_ssml.encode('utf-8'),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Azure TTS connection test successful")
                return True
            else:
                self.logger.error(f"Connection test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection test error: {e}")
            return False
