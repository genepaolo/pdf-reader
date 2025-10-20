# Azure TTS Client Usage Examples

## Environment Variables

The Azure TTS client supports two ways to configure the endpoint:

### Option 1: Region-based (Default)
```bash
# .env file
AZURE_TTS_SUBSCRIPTION_KEY=your-subscription-key-here
AZURE_TTS_REGION=westus  # Optional, defaults to 'westus'
```

### Option 2: Custom Endpoint (Your case)
```bash
# .env file
AZURE_TTS_SUBSCRIPTION_KEY=your-subscription-key-here
AZURE_ENDPOINT=https://your-custom-endpoint.cognitiveservices.azure.com
```

## Usage Examples

### Basic Usage
```python
from tts_pipeline.api.azure_tts_client import AzureTTSClient

# Initialize client (will use AZURE_ENDPOINT if set, otherwise region-based)
client = AzureTTSClient()

# Test connection
if client.test_connection():
    print("✅ Azure TTS connection successful!")
    
    # Get voice info
    voice_info = client.get_voice_info()
    print(f"Using endpoint: {voice_info['base_url']}")
    print(f"Voice: {voice_info['voice_name']}")
    
    # Convert text to speech
    success = client.synthesize_text(
        text="Hello, this is a test of Azure TTS!",
        output_path="output/test_audio.mp3"
    )
    
    if success:
        print("✅ Audio file generated successfully!")
    else:
        print("❌ Failed to generate audio file")
else:
    print("❌ Azure TTS connection failed")
```

### With Custom Config
```python
# Use a different config file
client = AzureTTSClient(config_path="path/to/custom_azure_config.json")
```

## Environment Variable Priority

1. **AZURE_ENDPOINT** - If set, uses this custom endpoint
2. **AZURE_TTS_REGION** - If AZURE_ENDPOINT not set, uses region-based URL
3. **Default region** - If neither set, defaults to 'westus'

## Your Setup

Since you have `AZURE_ENDPOINT` in your `.env` file, the client will:
- Use your custom endpoint instead of the region-based URL
- Automatically strip any trailing slashes from the endpoint
- Append `/cognitiveservices/v1` to create the synthesis URL

Example:
- Your endpoint: `https://my-endpoint.cognitiveservices.azure.com`
- Synthesis URL: `https://my-endpoint.cognitiveservices.azure.com/cognitiveservices/v1`
