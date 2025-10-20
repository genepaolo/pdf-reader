# Azure TTS Connectivity Testing

This document explains how to test your Azure TTS setup and verify connectivity to your endpoints.

## Quick Test Script

Run the connectivity test script to verify your setup:

```bash
cd tts_pipeline
python test_azure_connectivity.py
```

This script will:
- ✅ Check your environment variables
- ✅ Test endpoint priority logic
- ✅ Verify Azure TTS client initialization
- ✅ Test actual connection (if credentials are available)

## Comprehensive Test Suite

Run the full test suite with pytest:

```bash
# Run all Azure TTS tests
python -m pytest tts_pipeline/tests/unit/test_azure_tts_client.py tts_pipeline/tests/integration/test_azure_tts_connectivity.py -v

# Run only integration tests
python -m pytest tts_pipeline/tests/integration/test_azure_tts_connectivity.py -v

# Run tests with real Azure credentials (costs money)
python -m pytest tts_pipeline/tests/integration/test_azure_tts_connectivity.py::TestAzureTTSClientConnectivity::test_actual_tts_synthesis -v -m slow
```

## Test Types

### 1. Unit Tests (26 tests)
- **Location**: `tests/unit/test_azure_tts_client.py`
- **Purpose**: Test individual functions and components
- **Cost**: Free (uses mocked responses)
- **Run**: Always runs, no external dependencies

### 2. Integration Tests (8 tests)
- **Location**: `tests/integration/test_azure_tts_connectivity.py`
- **Purpose**: Test real connectivity and endpoint logic
- **Cost**: Free for logic tests, costs money for actual TTS calls
- **Run**: Logic tests always run, connectivity tests require real credentials

### 3. Connectivity Tests
- **Purpose**: Test actual Azure TTS API connectivity
- **Requirements**: Real `AZURE_TTS_SUBSCRIPTION_KEY` in environment
- **Cost**: Minimal (makes small test requests)
- **Skip**: Automatically skipped if no real credentials

## Environment Variables

The tests support these environment variables:

```bash
# Required for real connectivity tests
AZURE_TTS_SUBSCRIPTION_KEY=your-actual-subscription-key

# Optional - custom endpoint (takes priority)
AZURE_ENDPOINT=https://your-custom-endpoint.cognitiveservices.azure.com

# Optional - region (used if no custom endpoint)
AZURE_TTS_REGION=westus
```

## Test Results Interpretation

### ✅ All Tests Pass
Your Azure TTS setup is working correctly and ready for production use.

### ⚠️ Some Tests Skipped
- **Logic tests pass, connectivity tests skipped**: Normal if you don't have real Azure credentials set
- **Connectivity tests fail**: Check your credentials and endpoint configuration

### ❌ Tests Fail
- **Unit tests fail**: Code issue, needs fixing
- **Integration tests fail**: Configuration issue, check environment variables

## Cost Considerations

- **Unit tests**: Free (mocked responses)
- **Integration logic tests**: Free (no API calls)
- **Connectivity tests**: Minimal cost (small test requests)
- **Actual TTS synthesis test**: Costs money (real audio generation)

## Troubleshooting

### "Real Azure credentials not available"
- Set `AZURE_TTS_SUBSCRIPTION_KEY` in your environment
- Make sure it's not a test key (doesn't start with 'test-')

### "Connection test failed"
- Verify your subscription key is correct
- Check your endpoint URL format
- Ensure your Azure region supports TTS services
- Check your internet connection

### "Invalid endpoint" errors
- Ensure endpoint URL starts with `https://`
- Remove trailing slashes (they're handled automatically)
- Verify the endpoint is a valid Azure Cognitive Services endpoint

## Running Tests in CI/CD

For continuous integration, run only the free tests:

```bash
# Skip expensive tests
python -m pytest tts_pipeline/tests/unit/test_azure_tts_client.py tts_pipeline/tests/integration/test_azure_tts_connectivity.py -v -m "not slow"
```

This ensures your code works without incurring Azure costs in automated testing.
