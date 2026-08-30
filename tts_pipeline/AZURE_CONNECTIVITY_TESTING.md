# Azure TTS Connectivity Testing

*(The old standalone connectivity suite tested the pre-batch client and was
removed in the 2026-08-10 audit.)*

## Quick checks

```bash
# 1. Config + discovery sanity, no Azure calls, no billing:
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --dry-run --max-chapters 5

# 2. Unit tests for the batch client (mocked, no network):
cd tts_pipeline && py -3.12 -m pytest tests/unit/test_azure_tts_client.py -q

# 3. Live credential check (tests/test_azure_connectivity.py skips politely
#    when AZURE_TTS_SUBSCRIPTION_KEY / AZURE_TTS_REGION are absent):
cd tts_pipeline && py -3.12 -m pytest tests/test_azure_connectivity.py -q
```

## Troubleshooting

- `ValueError: Azure Speech credentials not found` → set
  `AZURE_TTS_SUBSCRIPTION_KEY` and `AZURE_TTS_REGION` in `.env`.
- 401/403 from the batch API → key/region mismatch (key is region-bound).
- Jobs stuck in `Running` → check the Azure portal Speech resource quota;
  batch jobs time out after `batch_timeout_minutes` (default 60).
