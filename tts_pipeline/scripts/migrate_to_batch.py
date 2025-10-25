#!/usr/bin/env python3
"""
Migration Utility for Batch Synthesis API

This script helps migrate projects from single-threaded to batch processing
with validation, testing, and rollback capabilities.

Features:
- Configuration validation
- Performance comparison
- Gradual migration support
- Rollback functionality
- Testing and validation

Usage:
    python scripts/migrate_to_batch.py --project lotm_book1 --validate
    python scripts/migrate_to_batch.py --project lotm_book1 --migrate
    python scripts/migrate_to_batch.py --project lotm_book1 --rollback
"""

import argparse
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.project_manager import ProjectManager, Project
from api.azure_tts_factory import AzureTTSFactory


class BatchMigrationManager:
    """Manages migration from single-threaded to batch processing."""
    
    def __init__(self, project: Project):
        """
        Initialize the migration manager.
        
        Args:
            project: Project object to migrate
        """
        self.project = project
        self.logger = logging.getLogger(__name__)
        self.migration_log = []
        
        self.logger.info(f"Initialized migration manager for project: {project.project_name}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate project configuration for batch processing.
        
        Returns:
            Validation results dictionary
        """
        self.logger.info("Validating project configuration for batch processing...")
        
        results = {
            'project_name': self.project.project_name,
            'validation_time': datetime.now().isoformat(),
            'single_threaded_valid': False,
            'batch_valid': False,
            'issues': [],
            'recommendations': []
        }
        
        # Validate single-threaded configuration
        try:
            single_valid = AzureTTSFactory.validate_mode_configuration(self.project, 'single')
            results['single_threaded_valid'] = single_valid
            
            if single_valid:
                self.logger.info("✓ Single-threaded configuration is valid")
            else:
                results['issues'].append("Single-threaded configuration has issues")
                self.logger.warning("✗ Single-threaded configuration has issues")
                
        except Exception as e:
            results['issues'].append(f"Error validating single-threaded config: {e}")
            self.logger.error(f"Error validating single-threaded config: {e}")
        
        # Validate batch configuration
        try:
            batch_valid = AzureTTSFactory.validate_mode_configuration(self.project, 'batch')
            results['batch_valid'] = batch_valid
            
            if batch_valid:
                self.logger.info("✓ Batch configuration is valid")
            else:
                results['issues'].append("Batch configuration has issues")
                self.logger.warning("✗ Batch configuration has issues")
                
        except Exception as e:
            results['issues'].append(f"Error validating batch config: {e}")
            self.logger.error(f"Error validating batch config: {e}")
        
        # Check for batch-specific configuration
        azure_processing = self.project.processing_config.get('azure_processing', {})
        if not azure_processing:
            results['issues'].append("No azure_processing configuration found")
            results['recommendations'].append("Add azure_processing configuration to processing_config.json")
        
        # Check batch size configuration
        batch_size = azure_processing.get('batch_size', 100)
        if batch_size <= 0 or batch_size > 10000:
            results['issues'].append(f"Invalid batch_size: {batch_size}")
            results['recommendations'].append("Set batch_size between 1 and 10000")
        
        # Check concurrent batches configuration
        max_concurrent_batches = azure_processing.get('max_concurrent_batches', 3)
        if max_concurrent_batches <= 0 or max_concurrent_batches > 10:
            results['issues'].append(f"Invalid max_concurrent_batches: {max_concurrent_batches}")
            results['recommendations'].append("Set max_concurrent_batches between 1 and 10")
        
        # Overall validation result
        results['overall_valid'] = results['single_threaded_valid'] and results['batch_valid'] and len(results['issues']) == 0
        
        if results['overall_valid']:
            self.logger.info("✓ Project is ready for batch processing migration")
        else:
            self.logger.warning("✗ Project has configuration issues that need to be resolved")
        
        return results
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """
        Get performance comparison between single-threaded and batch processing.
        
        Returns:
            Performance comparison dictionary
        """
        self.logger.info("Calculating performance comparison...")
        
        comparison = {
            'project_name': self.project.project_name,
            'comparison_time': datetime.now().isoformat(),
            'single_threaded': {},
            'batch': {},
            'improvement': {}
        }
        
        # Get performance estimates
        try:
            single_estimate = AzureTTSFactory.get_mode_performance_estimate(self.project, 'single')
            batch_estimate = AzureTTSFactory.get_mode_performance_estimate(self.project, 'batch')
            
            comparison['single_threaded'] = single_estimate
            comparison['batch'] = batch_estimate
            
            # Calculate improvements
            if 'error' not in single_estimate and 'error' not in batch_estimate:
                speedup = batch_estimate['chapters_per_hour'] / single_estimate['chapters_per_hour']
                api_reduction = 1 - (batch_estimate['api_calls_per_chapter'] / single_estimate['api_calls_per_chapter'])
                
                comparison['improvement'] = {
                    'speedup_factor': speedup,
                    'api_calls_reduction': api_reduction,
                    'time_savings_percentage': (1 - 1/speedup) * 100,
                    'cost_difference': batch_estimate['estimated_cost_per_month'] - single_estimate['estimated_cost_per_month']
                }
                
                self.logger.info(f"Performance improvement: {speedup:.1f}x faster")
                self.logger.info(f"API calls reduction: {api_reduction*100:.1f}%")
            
        except Exception as e:
            comparison['error'] = f"Error calculating performance comparison: {e}"
            self.logger.error(f"Error calculating performance comparison: {e}")
        
        return comparison
    
    def create_batch_configuration(self) -> bool:
        """
        Create batch-specific configuration for the project.
        
        Returns:
            True if configuration was created successfully
        """
        self.logger.info("Creating batch configuration...")
        
        try:
            # Get current processing config
            processing_config = self.project.processing_config.copy()
            
            # Add batch processing configuration
            azure_processing = processing_config.get('azure_processing', {})
            azure_processing.update({
                'mode': 'batch',
                'batch_size': 100,
                'max_concurrent_batches': 3,
                'batch_timeout_minutes': 60,
                'fallback_to_single': True,
                'retry_failed_batches': True,
                'max_batch_retries': 2
            })
            
            processing_config['azure_processing'] = azure_processing
            
            # Add batch optimization settings
            processing_config['batch_optimization'] = {
                'preload_chapter_texts': True,
                'validate_text_length': True,
                'compress_batch_requests': True,
                'parallel_download': True,
                'cleanup_temp_files': True
            }
            
            # Add monitoring settings
            processing_config['monitoring'] = {
                'log_batch_progress': True,
                'track_batch_performance': True,
                'alert_on_failures': True,
                'save_batch_logs': True
            }
            
            # Save updated configuration
            config_path = Path(self.project.project_dir) / 'processing_config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(processing_config, f, indent=2)
            
            self.logger.info("✓ Batch configuration created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating batch configuration: {e}")
            return False
    
    def migrate_to_batch(self) -> Dict[str, Any]:
        """
        Migrate project to batch processing.
        
        Returns:
            Migration results dictionary
        """
        self.logger.info("Starting migration to batch processing...")
        
        results = {
            'project_name': self.project.project_name,
            'migration_time': datetime.now().isoformat(),
            'success': False,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Validate configuration
            self.logger.info("Step 1: Validating configuration...")
            validation = self.validate_configuration()
            
            if not validation['overall_valid']:
                results['errors'].append("Configuration validation failed")
                self.logger.error("Configuration validation failed, aborting migration")
                return results
            
            results['steps_completed'].append("Configuration validation")
            
            # Step 2: Create batch configuration
            self.logger.info("Step 2: Creating batch configuration...")
            if not self.create_batch_configuration():
                results['errors'].append("Failed to create batch configuration")
                self.logger.error("Failed to create batch configuration")
                return results
            
            results['steps_completed'].append("Batch configuration creation")
            
            # Step 3: Test batch client creation
            self.logger.info("Step 3: Testing batch client creation...")
            try:
                batch_client = AzureTTSFactory.create_client(self.project, 'batch')
                self.logger.info(f"✓ Batch client created: {type(batch_client).__name__}")
                results['steps_completed'].append("Batch client creation test")
            except Exception as e:
                results['errors'].append(f"Failed to create batch client: {e}")
                self.logger.error(f"Failed to create batch client: {e}")
                return results
            
            # Step 4: Update project configuration
            self.logger.info("Step 4: Updating project configuration...")
            self.project.processing_config['azure_processing']['mode'] = 'batch'
            results['steps_completed'].append("Project configuration update")
            
            # Migration completed successfully
            results['success'] = True
            self.logger.info("✓ Migration to batch processing completed successfully")
            
        except Exception as e:
            results['errors'].append(f"Migration failed: {e}")
            self.logger.error(f"Migration failed: {e}")
        
        return results
    
    def rollback_to_single(self) -> Dict[str, Any]:
        """
        Rollback project to single-threaded processing.
        
        Returns:
            Rollback results dictionary
        """
        self.logger.info("Starting rollback to single-threaded processing...")
        
        results = {
            'project_name': self.project.project_name,
            'rollback_time': datetime.now().isoformat(),
            'success': False,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Update project configuration
            self.logger.info("Step 1: Updating project configuration...")
            self.project.processing_config['azure_processing']['mode'] = 'single'
            results['steps_completed'].append("Project configuration update")
            
            # Step 2: Test single-threaded client creation
            self.logger.info("Step 2: Testing single-threaded client creation...")
            try:
                single_client = AzureTTSFactory.create_client(self.project, 'single')
                self.logger.info(f"✓ Single-threaded client created: {type(single_client).__name__}")
                results['steps_completed'].append("Single-threaded client creation test")
            except Exception as e:
                results['errors'].append(f"Failed to create single-threaded client: {e}")
                self.logger.error(f"Failed to create single-threaded client: {e}")
                return results
            
            # Rollback completed successfully
            results['success'] = True
            self.logger.info("✓ Rollback to single-threaded processing completed successfully")
            
        except Exception as e:
            results['errors'].append(f"Rollback failed: {e}")
            self.logger.error(f"Rollback failed: {e}")
        
        return results
    
    def test_batch_processing(self, test_chapters: int = 10) -> Dict[str, Any]:
        """
        Test batch processing with a small number of chapters.
        
        Args:
            test_chapters: Number of chapters to test with
            
        Returns:
            Test results dictionary
        """
        self.logger.info(f"Testing batch processing with {test_chapters} chapters...")
        
        results = {
            'project_name': self.project.project_name,
            'test_time': datetime.now().isoformat(),
            'test_chapters': test_chapters,
            'success': False,
            'test_results': {},
            'errors': []
        }
        
        try:
            # Import here to avoid circular imports
            from scripts.process_project_batch import BatchTTSProcessor
            
            # Create test processor
            processor = BatchTTSProcessor(self.project, dry_run=True)
            
            # Get test chapters
            chapters = processor.discover_chapters()
            test_chapters_list = chapters[:test_chapters]
            
            if len(test_chapters_list) < test_chapters:
                self.logger.warning(f"Only {len(test_chapters_list)} chapters available for testing")
                test_chapters_list = chapters
            
            # Run test
            test_results = processor.process_chapters_batch(test_chapters_list)
            
            results['test_results'] = test_results
            results['success'] = True
            
            self.logger.info("✓ Batch processing test completed successfully")
            
        except Exception as e:
            results['errors'].append(f"Test failed: {e}")
            self.logger.error(f"Batch processing test failed: {e}")
        
        return results


def main():
    """Main entry point for migration utility."""
    parser = argparse.ArgumentParser(
        description="Migrate TTS projects to batch processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate project configuration
  python scripts/migrate_to_batch.py --project lotm_book1 --validate
  
  # Show performance comparison
  python scripts/migrate_to_batch.py --project lotm_book1 --compare
  
  # Migrate to batch processing
  python scripts/migrate_to_batch.py --project lotm_book1 --migrate
  
  # Test batch processing
  python scripts/migrate_to_batch.py --project lotm_book1 --test
  
  # Rollback to single-threaded
  python scripts/migrate_to_batch.py --project lotm_book1 --rollback
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Project name to migrate'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate project configuration'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Show performance comparison'
    )
    
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate to batch processing'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test batch processing'
    )
    
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback to single-threaded processing'
    )
    
    parser.add_argument(
        '--test-chapters',
        type=int,
        default=10,
        help='Number of chapters to test with (default: 10)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load project
        project_manager = ProjectManager()
        project = project_manager.load_project(args.project)
        
        if not project:
            logging.error(f"Project not found: {args.project}")
            return 1
        
        # Initialize migration manager
        migration_manager = BatchMigrationManager(project)
        
        # Execute requested operations
        if args.validate:
            print("Validating Project Configuration")
            print("=" * 40)
            
            validation = migration_manager.validate_configuration()
            
            print(f"Project: {validation['project_name']}")
            print(f"Single-threaded valid: {'✓' if validation['single_threaded_valid'] else '✗'}")
            print(f"Batch valid: {'✓' if validation['batch_valid'] else '✗'}")
            print(f"Overall valid: {'✓' if validation['overall_valid'] else '✗'}")
            
            if validation['issues']:
                print("\nIssues:")
                for issue in validation['issues']:
                    print(f"  - {issue}")
            
            if validation['recommendations']:
                print("\nRecommendations:")
                for rec in validation['recommendations']:
                    print(f"  - {rec}")
            
            print()
        
        if args.compare:
            print("Performance Comparison")
            print("=" * 30)
            
            comparison = migration_manager.get_performance_comparison()
            
            if 'error' not in comparison:
                print(f"Single-threaded:")
                print(f"  Chapters per hour: {comparison['single_threaded']['chapters_per_hour']}")
                print(f"  API calls per chapter: {comparison['single_threaded']['api_calls_per_chapter']}")
                print(f"  Cost per month: ${comparison['single_threaded']['estimated_cost_per_month']}")
                
                print(f"\nBatch:")
                print(f"  Chapters per hour: {comparison['batch']['chapters_per_hour']}")
                print(f"  API calls per chapter: {comparison['batch']['api_calls_per_chapter']:.3f}")
                print(f"  Cost per month: ${comparison['batch']['estimated_cost_per_month']}")
                
                if 'improvement' in comparison:
                    print(f"\nImprovement:")
                    print(f"  Speedup: {comparison['improvement']['speedup_factor']:.1f}x")
                    print(f"  API reduction: {comparison['improvement']['api_calls_reduction']*100:.1f}%")
                    print(f"  Time savings: {comparison['improvement']['time_savings_percentage']:.1f}%")
                    print(f"  Cost difference: ${comparison['improvement']['cost_difference']}")
            else:
                print(f"Error: {comparison['error']}")
            
            print()
        
        if args.migrate:
            print("Migrating to Batch Processing")
            print("=" * 35)
            
            migration = migration_manager.migrate_to_batch()
            
            print(f"Project: {migration['project_name']}")
            print(f"Success: {'✓' if migration['success'] else '✗'}")
            
            if migration['steps_completed']:
                print("\nSteps completed:")
                for step in migration['steps_completed']:
                    print(f"  ✓ {step}")
            
            if migration['errors']:
                print("\nErrors:")
                for error in migration['errors']:
                    print(f"  ✗ {error}")
            
            print()
        
        if args.test:
            print("Testing Batch Processing")
            print("=" * 30)
            
            test = migration_manager.test_batch_processing(args.test_chapters)
            
            print(f"Project: {test['project_name']}")
            print(f"Test chapters: {test['test_chapters']}")
            print(f"Success: {'✓' if test['success'] else '✗'}")
            
            if test['errors']:
                print("\nErrors:")
                for error in test['errors']:
                    print(f"  ✗ {error}")
            
            print()
        
        if args.rollback:
            print("Rolling Back to Single-Threaded")
            print("=" * 35)
            
            rollback = migration_manager.rollback_to_single()
            
            print(f"Project: {rollback['project_name']}")
            print(f"Success: {'✓' if rollback['success'] else '✗'}")
            
            if rollback['steps_completed']:
                print("\nSteps completed:")
                for step in rollback['steps_completed']:
                    print(f"  ✓ {step}")
            
            if rollback['errors']:
                print("\nErrors:")
                for error in rollback['errors']:
                    print(f"  ✗ {error}")
            
            print()
        
        # If no specific operation requested, show help
        if not any([args.validate, args.compare, args.migrate, args.test, args.rollback]):
            print("No operation specified. Use --help for available options.")
            return 1
        
        return 0
        
    except Exception as e:
        logging.error(f"Error during migration: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
