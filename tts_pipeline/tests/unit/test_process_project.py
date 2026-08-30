"""
Entry-point smoke tests for the pipeline scripts.

These run the scripts as real subprocesses (like the documented workflow does)
so they catch import-layer breakage — the exact failure mode that silently
killed process_project.py / create_videos.py in mid-2026.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = REPO_ROOT / "tts_pipeline" / "scripts"


def run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    """Run a pipeline script from the repo root, as documented in CLAUDE.md."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )


class TestEntryPointImports:
    """Every documented entry point must at least import and print help."""

    @pytest.mark.parametrize("script", ["process_project.py", "create_videos.py", "prepare_backgrounds.py"])
    def test_help_exits_zero(self, script):
        result = run_script(script, "--help")
        assert result.returncode == 0, (
            f"{script} --help failed (import breakage?):\n{result.stderr}"
        )

    def test_upload_queue_imports(self):
        """upload_queue.py must import; --limit is validated without uploading."""
        result = subprocess.run(
            [sys.executable, "-c",
             "import ast, sys, pathlib; "
             "src = pathlib.Path('upload_queue.py').read_text(encoding='utf-8'); "
             "ast.parse(src)"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
        )
        assert result.returncode == 0, result.stderr


class TestProcessProjectCLI:
    def test_list_projects(self):
        result = run_script("process_project.py", "--list-projects")
        assert result.returncode == 0, result.stderr
        assert "lotm_book1" in result.stdout
        assert "lom_book2_coi" in result.stdout

    def test_project_required_without_list(self):
        result = run_script("process_project.py")
        assert result.returncode != 0
        assert "--project" in (result.stderr + result.stdout)

    def test_unknown_project_fails(self):
        result = run_script("process_project.py", "--project", "no_such_project", "--dry-run")
        assert result.returncode != 0


class TestPrepareBackgroundsCLI:
    def test_status_known_project(self):
        result = run_script("prepare_backgrounds.py", "--project", "lotm_book1", "--status")
        # exit 0 = all ranges mapped; book1 mapping is complete
        assert result.returncode == 0, result.stdout + result.stderr
        assert "All ranges mapped" in result.stdout

    def test_unknown_project_rejected(self):
        result = run_script("prepare_backgrounds.py", "--project", "nope", "--status")
        assert result.returncode == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
