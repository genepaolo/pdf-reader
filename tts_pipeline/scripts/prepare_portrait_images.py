#!/usr/bin/env python3
"""
Script to pre-resize all portrait images to 1920x1080 for optimal video creation performance.
This eliminates the need for real-time scaling during video creation.
"""

import os
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def resize_image(input_path: Path, output_path: Path) -> bool:
    """
    Resize an image to 1920x1080 with proper aspect ratio handling.
    
    Args:
        input_path: Path to the input image
        output_path: Path to the output resized image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg command to resize image with proper aspect ratio
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', str(input_path),  # Input image
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black',
            '-frames:v', '1',  # Single frame
            '-update', '1',  # Update single image
            str(output_path)
        ]
        
        logging.info(f"Resizing {input_path.name} -> {output_path.name}")
        
        # Execute FFmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logging.info(f"✓ Successfully resized: {output_path.name}")
            return True
        else:
            logging.error(f"✗ Failed to resize {input_path.name}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"✗ Timeout resizing {input_path.name}")
        return False
    except Exception as e:
        logging.error(f"✗ Error resizing {input_path.name}: {e}")
        return False

def main():
    """Main function to resize all portrait images."""
    setup_logging()
    
    # Define paths
    assets_dir = Path('./tts_pipeline/assets/images')
    resized_dir = assets_dir / 'resized'
    
    # Create resized directory
    resized_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all portrait images
    portrait_patterns = [
        'lotm_*.jpg',
        'lotm_*.png',
        'lotm_*.jpeg'
    ]
    
    portrait_files = []
    for pattern in portrait_patterns:
        portrait_files.extend(assets_dir.glob(pattern))
    
    if not portrait_files:
        logging.error("No portrait images found!")
        return
    
    logging.info(f"Found {len(portrait_files)} portrait images to resize")
    
    # Resize each image
    successful = 0
    failed = 0
    
    for image_path in portrait_files:
        # Create output filename
        output_filename = f"{image_path.stem}_1920x1080{image_path.suffix}"
        output_path = resized_dir / output_filename
        
        # Skip if already resized
        if output_path.exists():
            logging.info(f"⏭ Skipping {image_path.name} (already resized)")
            continue
        
        # Resize the image
        if resize_image(image_path, output_path):
            successful += 1
        else:
            failed += 1
    
    # Summary
    logging.info("=" * 60)
    logging.info("PORTRAIT IMAGE RESIZING SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Total images processed: {successful + failed}")
    logging.info(f"Successfully resized: {successful}")
    logging.info(f"Failed: {failed}")
    logging.info(f"Resized images location: {resized_dir}")
    logging.info("=" * 60)
    
    if failed > 0:
        logging.error(f"Failed to resize {failed} images")
        return 1
    
    logging.info("All portrait images successfully resized!")
    return 0

if __name__ == "__main__":
    exit(main())

