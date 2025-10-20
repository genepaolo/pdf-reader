"""
Project manager for handling TTS pipeline project configurations.

This module provides ProjectManager and Project classes for managing
project-based configurations, allowing different book series to have
different settings, narrators, and processing parameters.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProjectManager:
    """Manages project configurations and provides project discovery functionality."""
    
    def __init__(self, config_root: str = "./config/projects"):
        """
        Initialize the project manager.
        
        Args:
            config_root: Path to the projects configuration directory
        """
        self.config_root = Path(config_root)
        self.logger = logging.getLogger(__name__)
        
        # Ensure config root exists
        if not self.config_root.exists():
            self.logger.warning(f"Config root directory does not exist: {self.config_root}")
    
    def list_projects(self) -> List[str]:
        """
        List all available projects.
        
        Returns:
            List of project names found in the config directory
        """
        if not self.config_root.exists():
            return []
        
        projects = []
        for project_dir in self.config_root.iterdir():
            if project_dir.is_dir() and (project_dir / "project.json").exists():
                projects.append(project_dir.name)
        
        return sorted(projects)
    
    def load_project(self, project_name: str) -> Optional['Project']:
        """
        Load a specific project configuration.
        
        Args:
            project_name: Name of the project to load
            
        Returns:
            Project object if found and valid, None otherwise
        """
        project_path = self.config_root / project_name
        
        if not project_path.exists():
            self.logger.error(f"Project directory does not exist: {project_path}")
            return None
        
        try:
            project = Project(project_name, project_path)
            self.logger.info(f"Successfully loaded project: {project_name}")
            return project
        except Exception as e:
            self.logger.error(f"Failed to load project {project_name}: {e}")
            return None
    
    def validate_project(self, project_name: str) -> bool:
        """
        Validate that a project configuration is complete and valid.
        
        Args:
            project_name: Name of the project to validate
            
        Returns:
            True if project is valid, False otherwise
        """
        project = self.load_project(project_name)
        return project is not None and project.is_valid()
    
    def create_project(self, project_name: str, template: str = "default") -> bool:
        """
        Create a new project from a template.
        
        Args:
            project_name: Name of the project to create
            template: Template to use (currently only "default" supported)
            
        Returns:
            True if project was created successfully, False otherwise
        """
        if template != "default":
            self.logger.error(f"Unsupported template: {template}")
            return False
        
        project_path = self.config_root / project_name
        
        if project_path.exists():
            self.logger.error(f"Project already exists: {project_name}")
            return False
        
        try:
            # Create project directory
            project_path.mkdir(parents=True)
            
            # Create project.json
            project_config = {
                "project_name": project_name,
                "display_name": project_name.replace("_", " ").title(),
                "input_directory": f"../extracted_text/{project_name}",
                "output_directory": f"D:/{project_name}_output",
                "description": f"TTS project for {project_name}",
                "metadata": {
                    "series": "Unknown",
                    "book_number": 1,
                    "total_volumes": 1,
                    "total_chapters": 0,
                    "language": "en-US",
                    "genre": "unknown"
                },
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
            
            with open(project_path / "project.json", "w") as f:
                json.dump(project_config, f, indent=2)
            
            # Copy default configurations
            defaults_path = Path("./config/defaults")
            for config_file in ["azure_config.json", "processing_config.json", "video_config.json"]:
                default_config_path = defaults_path / config_file
                if default_config_path.exists():
                    with open(default_config_path, "r") as f:
                        config_data = f.read()
                    
                    # Replace placeholders
                    config_data = config_data.replace("{project_name}", project_name)
                    
                    with open(project_path / config_file, "w") as f:
                        f.write(config_data)
            
            self.logger.info(f"Successfully created project: {project_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create project {project_name}: {e}")
            return False


class Project:
    """Represents a single TTS project with its configurations."""
    
    def __init__(self, project_name: str, config_path: Path):
        """
        Initialize a project.
        
        Args:
            project_name: Name of the project
            config_path: Path to the project configuration directory
        """
        self.project_name = project_name
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self.project_config = self._load_project_config()
        self.azure_config = self._load_azure_config()
        self.processing_config = self._load_processing_config()
        self.video_config = self._load_video_config()
    
    def _load_project_config(self) -> Dict[str, Any]:
        """Load project.json configuration."""
        config_file = self.config_path / "project.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load project config: {e}")
            return {}
    
    def _load_azure_config(self) -> Dict[str, Any]:
        """Load Azure TTS configuration."""
        config_file = self.config_path / "azure_config.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load Azure config: {e}")
            return {}
    
    def _load_processing_config(self) -> Dict[str, Any]:
        """Load processing configuration."""
        config_file = self.config_path / "processing_config.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load processing config: {e}")
            return {}
    
    def _load_video_config(self) -> Dict[str, Any]:
        """Load video configuration."""
        config_file = self.config_path / "video_config.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load video config: {e}")
            return {}
    
    def get_input_directory(self) -> Path:
        """Get input directory for this project."""
        input_dir = self.project_config.get("input_directory", "")
        return Path(input_dir)
    
    def get_output_directory(self) -> Path:
        """Get output directory for this project."""
        output_dir = self.project_config.get("output_directory", "")
        return Path(output_dir)
    
    def get_azure_config(self) -> Dict[str, Any]:
        """Get Azure TTS configuration."""
        return self.azure_config.copy()
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.processing_config.copy()
    
    def get_video_config(self) -> Dict[str, Any]:
        """Get video configuration."""
        return self.video_config.copy()
    
    def get_tracking_file(self) -> Path:
        """Get progress tracking file path for this project."""
        return Path("./tracking") / f"{self.project_name}_progress.json"
    
    def get_completed_file(self) -> Path:
        """Get completed chapters file path for this project."""
        return Path("./tracking") / f"{self.project_name}_completed.json"
    
    def get_display_name(self) -> str:
        """Get display name for this project."""
        return self.project_config.get("display_name", self.project_name)
    
    def get_description(self) -> str:
        """Get project description."""
        return self.project_config.get("description", "")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get project metadata."""
        return self.project_config.get("metadata", {})
    
    def is_valid(self) -> bool:
        """
        Check if the project configuration is valid.
        
        Returns:
            True if project is valid, False otherwise
        """
        required_configs = ["project_config", "azure_config", "processing_config"]
        
        for config_name in required_configs:
            config = getattr(self, config_name)
            if not config:
                self.logger.error(f"Missing or invalid {config_name}")
                return False
        
        # Check required project config fields
        required_fields = ["project_name", "input_directory", "output_directory"]
        for field in required_fields:
            if field not in self.project_config:
                self.logger.error(f"Missing required field in project config: {field}")
                return False
        
        return True
    
    def update_last_modified(self):
        """Update the last_modified timestamp in project.json."""
        self.project_config["last_modified"] = datetime.now().isoformat()
        
        try:
            with open(self.config_path / "project.json", "w") as f:
                json.dump(self.project_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to update project timestamp: {e}")
    
    def __str__(self) -> str:
        """String representation of the project."""
        return f"Project({self.project_name}, {self.get_display_name()})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the project."""
        return f"Project(name='{self.project_name}', path='{self.config_path}', valid={self.is_valid()})"
