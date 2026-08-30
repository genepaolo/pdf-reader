"""
Unit tests for the live Azure Batch Synthesis client API.

Covers BatchJobManager SSML generation, AzureTTSClient construction (credential
handling, config plumbing), output-directory resolution (project layout vs.
legacy book1 fallback), and the factory. No network calls.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from api.azure_tts_client import AzureTTSClient, BatchJobManager
from api.azure_tts_factory import AzureTTSFactory


TEST_ENV = {
    "AZURE_TTS_SUBSCRIPTION_KEY": "test_key_12345",
    "AZURE_TTS_REGION": "eastus",
}


def make_mock_project(processing_overrides=None):
    project = MagicMock()
    project.project_name = "test_project"
    project.get_azure_config.return_value = {
        "voice_name": "en-US-SteffanNeural",
        "language": "en-US",
        "rate": "+0%",
        "pitch": "+0Hz",
    }
    processing = {"batch_size": 50, "max_concurrent_batches": 2}
    processing.update(processing_overrides or {})
    project.processing_config = processing
    return project


class TestBatchJobManagerSSML:
    def setup_method(self):
        self.manager = BatchJobManager("key", "eastus")

    def test_create_ssml_basic(self):
        ssml = self.manager._create_ssml("Hello world", {"voice_name": "en-US-JennyNeural"})
        assert "<speak" in ssml and "</speak>" in ssml
        assert "en-US-JennyNeural" in ssml
        assert "Hello world" in ssml

    def test_create_ssml_escapes_xml(self):
        ssml = self.manager._create_ssml("Fish & Chips <best> ever", {})
        assert "&amp;" in ssml
        assert "&lt;best&gt;" in ssml
        assert "<best>" not in ssml

    def test_create_ssml_defaults(self):
        ssml = self.manager._create_ssml("text", {})
        assert "en-US-SteffanNeural" in ssml  # default voice
        assert "xml:lang='en-US'" in ssml

    def test_base_url_uses_region(self):
        assert "eastus" in self.manager.base_url


class TestAzureTTSClientInit:
    def test_requires_credentials(self):
        project = make_mock_project()
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items()
                   if k not in ("AZURE_TTS_SUBSCRIPTION_KEY", "AZURE_TTS_REGION")}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="credentials"):
                    AzureTTSClient(project)

    def test_init_with_credentials(self):
        project = make_mock_project()
        with patch.dict(os.environ, TEST_ENV):
            client = AzureTTSClient(project)
        assert client.batch_size == 50
        assert client.max_concurrent_batches == 2
        assert isinstance(client.job_manager, BatchJobManager)

    def test_batch_config_defaults(self):
        project = make_mock_project()
        project.processing_config = {}
        with patch.dict(os.environ, TEST_ENV):
            client = AzureTTSClient(project)
        assert client.batch_size == 100
        assert client.max_concurrent_batches == 3


class TestOutputVolumeDirectory:
    """Audio placement: project layout preferred, legacy book1 mapping as fallback."""

    def _client(self):
        with patch.dict(os.environ, TEST_ENV):
            return AzureTTSClient(make_mock_project())

    def test_uses_discovered_volume_name(self, tmp_path):
        client = self._client()
        chapter = {"filename": "Chapter_5_Test.txt", "volume_name": "Volume_1_Nightmare"}
        result = client._get_output_volume_directory(chapter, tmp_path)
        assert result == tmp_path / "Volume_1_Nightmare"

    def test_legacy_fallback_without_volume_name(self, tmp_path):
        client = self._client()
        chapter = {"filename": "Chapter_5_Test.txt"}
        result = client._get_output_volume_directory(chapter, tmp_path)
        assert result == tmp_path / "1___VOLUME_1___CLOWN"

    def test_legacy_fallback_side_stories(self, tmp_path):
        client = self._client()
        chapter = {"filename": "Chapter_1400_Test.txt"}
        result = client._get_output_volume_directory(chapter, tmp_path)
        assert result == tmp_path / "Side_Stories"


class TestFactory:
    def test_factory_returns_batch_client(self):
        project = make_mock_project()
        with patch.dict(os.environ, TEST_ENV):
            client = AzureTTSFactory.create_client(project)
        assert isinstance(client, AzureTTSClient)

    def test_factory_propagates_credential_error(self):
        project = make_mock_project()
        env = {k: v for k, v in os.environ.items()
               if k not in ("AZURE_TTS_SUBSCRIPTION_KEY", "AZURE_TTS_REGION")}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError):
                AzureTTSFactory.create_client(project)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
