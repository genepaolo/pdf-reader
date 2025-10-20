"""
Unit tests for the project manager functionality.

Tests the ProjectManager and Project classes for loading, validation,
and management of project-based configurations.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
from datetime import datetime

# Add the parent directory to Python path to import from utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.project_manager import ProjectManager, Project


class TestProjectManager:
    """Test cases for ProjectManager class."""
    
    def test_init_with_existing_config_root(self, tmp_path):
        """Test ProjectManager initialization with existing config root."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        pm = ProjectManager(str(config_root))
        assert pm.config_root == config_root
    
    def test_init_with_nonexistent_config_root(self, tmp_path):
        """Test ProjectManager initialization with nonexistent config root."""
        config_root = tmp_path / "nonexistent"
        
        pm = ProjectManager(str(config_root))
        assert pm.config_root == config_root
    
    def test_list_projects_empty(self, tmp_path):
        """Test listing projects when no projects exist."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        pm = ProjectManager(str(config_root))
        projects = pm.list_projects()
        
        assert projects == []
    
    def test_list_projects_with_valid_project(self, tmp_path):
        """Test listing projects with a valid project."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create a test project
        project_dir = config_root / "test_project"
        project_dir.mkdir()
        (project_dir / "project.json").write_text('{"project_name": "test_project"}')
        
        pm = ProjectManager(str(config_root))
        projects = pm.list_projects()
        
        assert projects == ["test_project"]
    
    def test_list_projects_ignores_invalid_directories(self, tmp_path):
        """Test that invalid directories are ignored when listing projects."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create valid project
        project_dir = config_root / "valid_project"
        project_dir.mkdir()
        (project_dir / "project.json").write_text('{"project_name": "valid_project"}')
        
        # Create invalid directory (no project.json)
        invalid_dir = config_root / "invalid_dir"
        invalid_dir.mkdir()
        
        pm = ProjectManager(str(config_root))
        projects = pm.list_projects()
        
        assert projects == ["valid_project"]
    
    def test_load_project_success(self, tmp_path):
        """Test successfully loading a project."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create a complete test project
        project_dir = config_root / "test_project"
        project_dir.mkdir()
        
        # Create project.json
        project_config = {
            "project_name": "test_project",
            "display_name": "Test Project",
            "input_directory": "../extracted_text/test_project",
            "output_directory": "D:/test_project_output",
            "description": "Test project"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create azure_config.json
        azure_config = {
            "voice_name": "en-US-SteffanNeural",
            "language": "en-US"
        }
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        # Create processing_config.json
        processing_config = {
            "max_text_length": 20000,
            "retry_attempts": 3
        }
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        # Create video_config.json
        video_config = {
            "enabled": True,
            "format": {"resolution": "1920x1080"}
        }
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        pm = ProjectManager(str(config_root))
        project = pm.load_project("test_project")
        
        assert project is not None
        assert project.project_name == "test_project"
        assert project.is_valid()
    
    def test_load_project_nonexistent(self, tmp_path):
        """Test loading a nonexistent project."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        pm = ProjectManager(str(config_root))
        project = pm.load_project("nonexistent_project")
        
        assert project is None
    
    def test_load_project_invalid_config(self, tmp_path):
        """Test loading a project with invalid configuration."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create project directory with invalid JSON
        project_dir = config_root / "invalid_project"
        project_dir.mkdir()
        (project_dir / "project.json").write_text('{"invalid": json}')
        
        pm = ProjectManager(str(config_root))
        project = pm.load_project("invalid_project")
        
        # Project object is created but invalid
        assert project is not None
        assert not project.is_valid()
    
    def test_validate_project_success(self, tmp_path):
        """Test validating a valid project."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create a complete test project (same as test_load_project_success)
        project_dir = config_root / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "display_name": "Test Project",
            "input_directory": "../extracted_text/test_project",
            "output_directory": "D:/test_project_output"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        azure_config = {"voice_name": "en-US-SteffanNeural"}
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        processing_config = {"max_text_length": 20000}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        pm = ProjectManager(str(config_root))
        is_valid = pm.validate_project("test_project")
        
        assert is_valid
    
    def test_validate_project_invalid(self, tmp_path):
        """Test validating an invalid project."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        pm = ProjectManager(str(config_root))
        is_valid = pm.validate_project("nonexistent_project")
        
        assert not is_valid
    
    def test_create_project_success(self, tmp_path):
        """Test successfully creating a project from template."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create defaults directory with templates
        defaults_dir = tmp_path / "config" / "defaults"
        defaults_dir.mkdir(parents=True)
        
        # Create default templates
        (defaults_dir / "azure_config.json").write_text('{"voice_name": "en-US-SteffanNeural"}')
        (defaults_dir / "processing_config.json").write_text('{"max_text_length": 20000}')
        (defaults_dir / "video_config.json").write_text('{"enabled": true}')
        
        pm = ProjectManager(str(config_root))
        
        with patch('utils.project_manager.Path') as mock_path:
            mock_path.side_effect = lambda x: tmp_path / "config" / "defaults" if "defaults" in str(x) else Path(x)
            
            success = pm.create_project("new_project")
            assert success
            
            # Verify project was created
            projects = pm.list_projects()
            assert "new_project" in projects
    
    def test_create_project_already_exists(self, tmp_path):
        """Test creating a project that already exists."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        # Create existing project
        project_dir = config_root / "existing_project"
        project_dir.mkdir()
        (project_dir / "project.json").write_text('{"project_name": "existing_project"}')
        
        pm = ProjectManager(str(config_root))
        success = pm.create_project("existing_project")
        
        assert not success
    
    def test_create_project_invalid_template(self, tmp_path):
        """Test creating a project with invalid template."""
        config_root = tmp_path / "projects"
        config_root.mkdir()
        
        pm = ProjectManager(str(config_root))
        success = pm.create_project("new_project", template="invalid_template")
        
        assert not success


class TestProject:
    """Test cases for Project class."""
    
    def test_init_success(self, tmp_path):
        """Test successful Project initialization."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create project configuration files
        project_config = {
            "project_name": "test_project",
            "display_name": "Test Project",
            "input_directory": "../extracted_text/test_project",
            "output_directory": "D:/test_project_output",
            "description": "Test project",
            "metadata": {"series": "Test Series"}
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        azure_config = {"voice_name": "en-US-SteffanNeural", "language": "en-US"}
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        processing_config = {"max_text_length": 20000, "retry_attempts": 3}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        video_config = {"enabled": True, "format": {"resolution": "1920x1080"}}
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        project = Project("test_project", project_dir)
        
        assert project.project_name == "test_project"
        assert project.config_path == project_dir
        assert project.project_config["project_name"] == "test_project"
        assert project.azure_config["voice_name"] == "en-US-SteffanNeural"
        assert project.processing_config["max_text_length"] == 20000
        assert project.video_config["enabled"] == True
    
    def test_get_input_directory(self, tmp_path):
        """Test getting input directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "input_directory": "../extracted_text/test_project"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        input_dir = project.get_input_directory()
        # Use pathlib comparison to handle OS differences
        expected_path = Path("../extracted_text/test_project")
        assert input_dir == expected_path
    
    def test_get_output_directory(self, tmp_path):
        """Test getting output directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "output_directory": "D:/test_project_output"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        output_dir = project.get_output_directory()
        # Use pathlib comparison to handle OS differences
        expected_path = Path("D:/test_project_output")
        assert output_dir == expected_path
    
    def test_get_configurations(self, tmp_path):
        """Test getting configuration dictionaries."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {"project_name": "test_project"}
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        azure_config = {"voice_name": "en-US-SteffanNeural"}
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        processing_config = {"max_text_length": 20000}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        video_config = {"enabled": True}
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        project = Project("test_project", project_dir)
        
        # Test that returned configs are copies (not references)
        azure_config_copy = project.get_azure_config()
        azure_config_copy["voice_name"] = "modified"
        assert project.azure_config["voice_name"] == "en-US-SteffanNeural"  # Original unchanged
    
    def test_get_tracking_files(self, tmp_path):
        """Test getting tracking file paths."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {"project_name": "test_project"}
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        progress_file = project.get_tracking_file()
        completed_file = project.get_completed_file()
        
        # Use pathlib comparison to handle OS differences
        expected_progress = Path("./tracking/test_project_progress.json")
        expected_completed = Path("./tracking/test_project_completed.json")
        assert progress_file == expected_progress
        assert completed_file == expected_completed
    
    def test_get_metadata(self, tmp_path):
        """Test getting project metadata."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "display_name": "Test Project",
            "description": "Test description",
            "metadata": {
                "series": "Test Series",
                "genre": "fantasy"
            }
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        assert project.get_display_name() == "Test Project"
        assert project.get_description() == "Test description"
        assert project.get_metadata()["series"] == "Test Series"
    
    def test_is_valid_success(self, tmp_path):
        """Test project validation with valid configuration."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "input_directory": "../extracted_text/test_project",
            "output_directory": "D:/test_project_output"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        azure_config = {"voice_name": "en-US-SteffanNeural"}
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        processing_config = {"max_text_length": 20000}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        video_config = {"enabled": True}
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        project = Project("test_project", project_dir)
        
        assert project.is_valid()
    
    def test_is_valid_missing_config(self, tmp_path):
        """Test project validation with missing configuration."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {"project_name": "test_project"}
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Missing azure_config.json
        processing_config = {"max_text_length": 20000}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        video_config = {"enabled": True}
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        project = Project("test_project", project_dir)
        
        assert not project.is_valid()
    
    def test_is_valid_missing_required_field(self, tmp_path):
        """Test project validation with missing required fields."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project"
            # Missing input_directory and output_directory
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        azure_config = {"voice_name": "en-US-SteffanNeural"}
        (project_dir / "azure_config.json").write_text(json.dumps(azure_config))
        
        processing_config = {"max_text_length": 20000}
        (project_dir / "processing_config.json").write_text(json.dumps(processing_config))
        
        video_config = {"enabled": True}
        (project_dir / "video_config.json").write_text(json.dumps(video_config))
        
        project = Project("test_project", project_dir)
        
        assert not project.is_valid()
    
    def test_update_last_modified(self, tmp_path):
        """Test updating the last_modified timestamp."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "last_modified": "2024-01-01T00:00:00"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        # Update timestamp
        project.update_last_modified()
        
        # Verify timestamp was updated
        updated_config = json.loads((project_dir / "project.json").read_text())
        assert updated_config["last_modified"] != "2024-01-01T00:00:00"
    
    def test_string_representations(self, tmp_path):
        """Test string representations of the project."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        project_config = {
            "project_name": "test_project",
            "display_name": "Test Project"
        }
        (project_dir / "project.json").write_text(json.dumps(project_config))
        
        # Create minimal config files
        (project_dir / "azure_config.json").write_text('{}')
        (project_dir / "processing_config.json").write_text('{}')
        (project_dir / "video_config.json").write_text('{}')
        
        project = Project("test_project", project_dir)
        
        str_repr = str(project)
        repr_str = repr(project)
        
        assert "test_project" in str_repr
        assert "Test Project" in str_repr
        assert "test_project" in repr_str
        assert "valid=" in repr_str


if __name__ == "__main__":
    pytest.main([__file__])
