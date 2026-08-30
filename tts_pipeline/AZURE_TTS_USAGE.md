# Azure TTS Usage

The pipeline uses the Azure **Batch Synthesis** API exclusively (the old
single-request client and its `AzureTTSClient(config_path=...)` constructor
were removed in the 2025 batch migration).

## Credentials (environment)

```
AZURE_TTS_SUBSCRIPTION_KEY=<key>
AZURE_TTS_REGION=<region, e.g. eastus>
```

Set them in `.env` at the repo root (loaded automatically by the scripts).
The client raises `ValueError` at construction if either is missing.

## Voice settings (per project)

`tts_pipeline/config/projects/<project>/azure_config.json` (gitignored —
copy `azure_config.json.example`): `voice_name`, `language`, `rate`, `pitch`.

## Programmatic use

```python
# entry points put tts_pipeline/ on sys.path
from utils.project_manager import ProjectManager
from api.azure_tts_factory import AzureTTSFactory

project = ProjectManager().load_project("lom_book2_coi")
client = AzureTTSFactory.create_client(project)   # AzureTTSClient(project)
results = client.process_chapters_batch(chapters) # chapters from ChapterFileOrganizer
```

Batch knobs in `processing_config.json`: `azure_processing.batch_size`,
`max_concurrent_batches`, `batch_timeout_minutes`; optional
`pronunciation_substitutions` / `pronunciation_disable_defaults`.

## Normal operation

Don't call the client directly — use the script:

```bash
py -3.12 tts_pipeline/scripts/process_project.py --project <p> --chapters N-M
```

`--dry-run` validates discovery/config without hitting Azure (no billing).
