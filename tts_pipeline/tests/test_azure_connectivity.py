#!/usr/bin/env python3
"""
Azure TTS Connectivity Test Script

This script tests your Azure TTS setup without making expensive TTS calls.
It verifies authentication, endpoint configuration, and basic connectivity.

Usage:
    python test_azure_connectivity.py

Environment Variables Required:
    AZURE_TTS_SUBSCRIPTION_KEY - Your Azure subscription key
    AZURE_ENDPOINT (optional) - Your custom Azure endpoint
    AZURE_TTS_REGION (optional) - Azure region (defaults to 'westus')
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to Python path to import from tts_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.azure_tts_client import AzureTTSClient


def test_azure_setup():
    """Test Azure TTS setup and connectivity."""
    print("Testing Azure TTS Setup...")
    print("=" * 50)
    
    # Check environment variables
    subscription_key = os.getenv('AZURE_TTS_SUBSCRIPTION_KEY')
    custom_endpoint = os.getenv('AZURE_ENDPOINT')
    region = os.getenv('AZURE_TTS_REGION', 'westus')
    
    print("Environment Variables:")
    print(f"   AZURE_TTS_SUBSCRIPTION_KEY: {'Set' if subscription_key else 'Not set'}")
    print(f"   AZURE_ENDPOINT: {'Set' if custom_endpoint else 'Not set'}")
    print(f"   AZURE_TTS_REGION: {region}")
    
    if not subscription_key:
        print("\nERROR: AZURE_TTS_SUBSCRIPTION_KEY is required!")
        print("   Please set it in your .env file or environment.")
        return False
    
    try:
        # Initialize client
        print("\nInitializing Azure TTS Client...")
        client = AzureTTSClient()
        
        # Get voice info
        voice_info = client.get_voice_info()
        print("\nVoice Configuration:")
        print(f"   Voice: {voice_info['voice_name']}")
        print(f"   Language: {voice_info['language']}")
        print(f"   Gender: {voice_info['gender']}")
        print(f"   Output Format: {voice_info['output_format']}")
        print(f"   Max Text Length: {voice_info['max_text_length']} chars")
        
        print("\nEndpoint Configuration:")
        if voice_info['endpoint']:
            print(f"   Using Custom Endpoint: {voice_info['endpoint']}")
        else:
            print(f"   Using Region-based URL: {voice_info['base_url']}")
        
        # Test connection
        print("\nTesting Connection...")
        connection_result = client.test_connection()
        
        if connection_result:
            print("Connection Test: SUCCESS")
            print("   Your Azure TTS setup is working correctly!")
            return True
        else:
            print("Connection Test: FAILED")
            print("   Please check your credentials and endpoint configuration.")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def test_endpoint_priority():
    """Test endpoint priority logic."""
    print("\nTesting Endpoint Priority Logic...")
    print("-" * 30)
    
    # Test cases
    test_cases = [
        {
            'name': 'Custom Endpoint Priority',
            'env': {
                'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
                'AZURE_ENDPOINT': 'https://custom.cognitiveservices.azure.com',
                'AZURE_TTS_REGION': 'eastus'
            },
            'expected_endpoint': 'https://custom.cognitiveservices.azure.com'
        },
        {
            'name': 'Region Fallback',
            'env': {
                'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key',
                'AZURE_TTS_REGION': 'westus2'
            },
            'expected_endpoint': None
        },
        {
            'name': 'Default Region',
            'env': {
                'AZURE_TTS_SUBSCRIPTION_KEY': 'test-key'
            },
            'expected_endpoint': None
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   Testing: {test_case['name']}")
        
        # Temporarily set environment variables
        original_env = {}
        for key, value in test_case['env'].items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            client = AzureTTSClient()
            voice_info = client.get_voice_info()
            
            if test_case['expected_endpoint']:
                if voice_info['endpoint'] == test_case['expected_endpoint']:
                    print(f"   PASS: Using custom endpoint")
                else:
                    print(f"   FAIL: Expected {test_case['expected_endpoint']}, got {voice_info['endpoint']}")
            else:
                if voice_info['endpoint'] is None:
                    print(f"   PASS: Using region-based URL: {voice_info['base_url']}")
                else:
                    print(f"   FAIL: Expected region-based URL, got custom endpoint: {voice_info['endpoint']}")
                    
        except Exception as e:
            print(f"   ERROR: {e}")
        
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


def main():
    """Main test function."""
    print("Azure TTS Connectivity Test")
    print("=" * 50)
    
    # Test basic setup
    setup_success = test_azure_setup()
    
    # Test endpoint priority (always runs)
    test_endpoint_priority()
    
    print(f"\n{'=' * 50}")
    if setup_success:
        print("All tests completed successfully!")
        print("   Your Azure TTS setup is ready to use.")
    else:
        print("Some tests failed.")
        print("   Please check your configuration and try again.")
    
    print(f"\nTips:")
    print(f"   - Make sure your .env file is in the project root")
    print(f"   - Verify your Azure subscription key is correct")
    print(f"   - Check that your endpoint URL is properly formatted")
    print(f"   - Ensure your Azure region supports TTS services")


if __name__ == "__main__":
    main()
