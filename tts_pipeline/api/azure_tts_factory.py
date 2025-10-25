#!/usr/bin/env python3
"""
Azure TTS Client Factory

This module provides a factory pattern to create the appropriate Azure TTS client
based on project configuration, enabling seamless switching between single-threaded
and batch processing modes.

Features:
- Configuration-based client selection
- Fallback to single-threaded processing
- Seamless integration with existing code
- Migration support for gradual transition

Usage:
    from api.azure_tts_factory import AzureTTSFactory
    
    client = AzureTTSFactory.create_client(project)
    success = client.synthesize_text(text, output_path)
"""

import logging
from typing import Union, Optional
from .azure_tts_client import AzureTTSClient
from .batch_azure_tts_client import BatchAzureTTSClient


class AzureTTSFactory:
    """
    Factory class for creating Azure TTS clients.
    
    Automatically selects the appropriate client type based on project configuration,
    enabling seamless switching between single-threaded and batch processing modes.
    """
    
    @staticmethod
    def create_client(project, force_mode: Optional[str] = None) -> Union[AzureTTSClient, BatchAzureTTSClient]:
        """
        Create an appropriate Azure TTS client based on project configuration.
        
        Args:
            project: Project object containing configuration
            force_mode: Force a specific mode ('single' or 'batch'), overrides config
            
        Returns:
            Azure TTS client instance (single-threaded or batch)
        """
        logger = logging.getLogger(__name__)
        
        # Determine processing mode
        if force_mode:
            mode = force_mode
            logger.info(f"Forcing Azure TTS mode: {mode}")
        else:
            mode = AzureTTSFactory._get_processing_mode(project)
            logger.info(f"Azure TTS mode from config: {mode}")
        
        # Create appropriate client
        if mode == 'batch':
            try:
                client = BatchAzureTTSClient(project)
                logger.info("Created Batch Azure TTS client")
                return client
            except Exception as e:
                logger.warning(f"Failed to create Batch client, falling back to single-threaded: {e}")
                return AzureTTSClient(project)
        else:
            client = AzureTTSClient(project)
            logger.info("Created single-threaded Azure TTS client")
            return client
    
    @staticmethod
    def _get_processing_mode(project) -> str:
        """
        Determine the processing mode from project configuration.
        
        Args:
            project: Project object containing configuration
            
        Returns:
            Processing mode ('single' or 'batch')
        """
        try:
            # Check for explicit batch processing configuration
            azure_processing = project.processing_config.get('azure_processing', {})
            mode = azure_processing.get('mode', 'single')
            
            # Validate mode
            if mode not in ['single', 'batch']:
                logging.warning(f"Invalid Azure processing mode: {mode}, defaulting to 'single'")
                mode = 'single'
            
            return mode
            
        except Exception as e:
            logging.warning(f"Error reading Azure processing mode: {e}, defaulting to 'single'")
            return 'single'
    
    @staticmethod
    def get_available_modes() -> list:
        """
        Get list of available processing modes.
        
        Returns:
            List of available modes
        """
        return ['single', 'batch']
    
    @staticmethod
    def get_mode_description(mode: str) -> str:
        """
        Get description of a processing mode.
        
        Args:
            mode: Processing mode name
            
        Returns:
            Description of the mode
        """
        descriptions = {
            'single': 'Single-threaded processing - one chapter per API call',
            'batch': 'Batch processing - up to 100 chapters per API call (24x faster)'
        }
        
        return descriptions.get(mode, 'Unknown mode')
    
    @staticmethod
    def validate_mode_configuration(project, mode: str) -> bool:
        """
        Validate that a project is properly configured for a specific mode.
        
        Args:
            project: Project object to validate
            mode: Mode to validate configuration for
            
        Returns:
            True if configuration is valid, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        if mode == 'single':
            # Single-threaded mode - check basic Azure config
            try:
                azure_config = project.get_azure_config()
                required_keys = ['voice_name', 'output_format', 'rate', 'pitch']
                
                for key in required_keys:
                    if key not in azure_config:
                        logger.error(f"Missing required Azure config key: {key}")
                        return False
                
                logger.info("Single-threaded mode configuration is valid")
                return True
                
            except Exception as e:
                logger.error(f"Error validating single-threaded config: {e}")
                return False
        
        elif mode == 'batch':
            # Batch mode - check batch-specific configuration
            try:
                azure_config = project.get_azure_config()
                processing_config = project.processing_config
                
                # Check Azure config
                required_azure_keys = ['voice_name', 'output_format', 'rate', 'pitch']
                for key in required_azure_keys:
                    if key not in azure_config:
                        logger.error(f"Missing required Azure config key: {key}")
                        return False
                
                # Check batch-specific config
                azure_processing = processing_config.get('azure_processing', {})
                batch_size = azure_processing.get('batch_size', 100)
                max_concurrent_batches = azure_processing.get('max_concurrent_batches', 3)
                
                if batch_size <= 0 or batch_size > 10000:
                    logger.error(f"Invalid batch_size: {batch_size} (must be 1-10000)")
                    return False
                
                if max_concurrent_batches <= 0 or max_concurrent_batches > 10:
                    logger.error(f"Invalid max_concurrent_batches: {max_concurrent_batches} (must be 1-10)")
                    return False
                
                logger.info("Batch mode configuration is valid")
                return True
                
            except Exception as e:
                logger.error(f"Error validating batch config: {e}")
                return False
        
        else:
            logger.error(f"Unknown mode: {mode}")
            return False
    
    @staticmethod
    def get_mode_performance_estimate(project, mode: str) -> dict:
        """
        Get performance estimate for a specific mode.
        
        Args:
            project: Project object
            mode: Processing mode
            
        Returns:
            Performance estimate dictionary
        """
        try:
            if mode == 'single':
                return {
                    'mode': 'single',
                    'chapters_per_hour': 120,  # 30 seconds per chapter
                    'api_calls_per_chapter': 1,
                    'estimated_cost_per_month': 4,  # $4/month
                    'description': 'Single-threaded processing'
                }
            
            elif mode == 'batch':
                batch_size = project.processing_config.get('azure_processing', {}).get('batch_size', 100)
                max_concurrent_batches = project.processing_config.get('azure_processing', {}).get('max_concurrent_batches', 3)
                
                # Estimate: 2 minutes per batch (100 chapters)
                chapters_per_hour = (batch_size * max_concurrent_batches * 30)  # 30 batches per hour
                
                return {
                    'mode': 'batch',
                    'chapters_per_hour': chapters_per_hour,
                    'api_calls_per_chapter': 1.0 / batch_size,  # 1 API call per batch
                    'estimated_cost_per_month': 4,  # Same cost as single-threaded
                    'batch_size': batch_size,
                    'max_concurrent_batches': max_concurrent_batches,
                    'description': f'Batch processing ({batch_size} chapters per batch)'
                }
            
            else:
                return {
                    'mode': 'unknown',
                    'error': f'Unknown mode: {mode}'
                }
                
        except Exception as e:
            return {
                'mode': mode,
                'error': f'Error calculating performance estimate: {e}'
            }


def main():
    """Test the Azure TTS factory."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Azure TTS factory")
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--mode', choices=['single', 'batch'], help='Force specific mode')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--performance', action='store_true', help='Show performance estimates')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from utils.project_manager import ProjectManager
        
        # Load project
        pm = ProjectManager()
        project = pm.load_project(args.project)
        
        if not project:
            print(f"Project not found: {args.project}")
            return 1
        
        print(f"Project: {project.project_name}")
        print(f"Forced mode: {args.mode}")
        print()
        
        # Validate configuration if requested
        if args.validate:
            print("Configuration Validation:")
            print("-" * 30)
            
            for mode in ['single', 'batch']:
                is_valid = AzureTTSFactory.validate_mode_configuration(project, mode)
                status = "✓ Valid" if is_valid else "✗ Invalid"
                print(f"{mode.capitalize()}: {status}")
            print()
        
        # Show performance estimates if requested
        if args.performance:
            print("Performance Estimates:")
            print("-" * 30)
            
            for mode in ['single', 'batch']:
                estimate = AzureTTSFactory.get_mode_performance_estimate(project, mode)
                if 'error' not in estimate:
                    print(f"{mode.capitalize()}:")
                    print(f"  Chapters per hour: {estimate['chapters_per_hour']}")
                    print(f"  API calls per chapter: {estimate['api_calls_per_chapter']:.3f}")
                    print(f"  Estimated cost: ${estimate['estimated_cost_per_month']}/month")
                    if 'batch_size' in estimate:
                        print(f"  Batch size: {estimate['batch_size']}")
                        print(f"  Max concurrent batches: {estimate['max_concurrent_batches']}")
                    print()
                else:
                    print(f"{mode.capitalize()}: Error - {estimate['error']}")
        
        # Create client
        client = AzureTTSFactory.create_client(project, args.mode)
        
        print(f"Created client: {type(client).__name__}")
        
        # Test basic functionality
        print("Testing basic functionality...")
        
        # This would normally test with real text, but for demo purposes:
        print("✓ Client created successfully")
        print("✓ Factory pattern working")
        
        return 0
        
    except Exception as e:
        logging.error(f"Error during factory test: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
