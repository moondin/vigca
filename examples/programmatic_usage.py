#!/usr/bin/env python
"""
Example of programmatic usage of ViGCA

This example demonstrates how to use ViGCA in a script without the GUI.
It performs the following steps:
1. Captures a screenshot
2. Adds a target from a specific region
3. Periodically scans for the target and moves the cursor when found
"""
import os
import time
import logging
import numpy as np
import cv2

from vigca.screen_capture import ScreenCapture
from vigca.feature_extraction import FeatureExtractor
from vigca.target_manager import TargetManager
from vigca.cursor_control import CursorController

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_target_image(image_path):
    """Load a target image from file."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Target image not found: {image_path}")
    
    # Load and convert to RGB
    image = cv2.imread(image_path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def main():
    """Main function for the example."""
    try:
        # Initialize components
        screen_capture = ScreenCapture(capture_rate=1.0)
        feature_extractor = FeatureExtractor(method="template_matching")
        feature_extractor.set_threshold(0.7)  # Lower threshold for better matching
        target_manager = TargetManager("example_targets.pkl")
        cursor_controller = CursorController(speed=5.0, smooth=True)
        
        # Capture initial screenshot
        logger.info("Capturing initial screenshot...")
        frame = screen_capture.capture(force=True)
        if frame is None:
            logger.error("Failed to capture screen")
            return
        
        # Method 1: Add target from captured screenshot region
        # Define a region in the screenshot (e.g., a button)
        x, y, width, height = 100, 100, 200, 50  # Example coordinates
        region = frame[y:y+height, x:x+width]
        
        # Method 2: Add target from an image file
        try:
            region = load_target_image("target_image.png")
        except FileNotFoundError as e:
            logger.warning(f"{e} - Using screen region instead")
        
        # Extract features and add target
        features = feature_extractor.extract_features(region)
        target_id = target_manager.add_target(
            name="Example Target",
            features=features,
            features_method=feature_extractor.method,
            bounding_box=(x, y, width, height),
            image=region
        )
        
        logger.info(f"Added target: {target_id}")
        
        # Main detection loop
        logger.info("Starting detection loop. Press Ctrl+C to exit.")
        try:
            while True:
                # Capture screen
                frame = screen_capture.capture()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Get target
                target = target_manager.get_target(target_id)
                
                # Find matches
                matches = feature_extractor.find_matches(target.features, frame)
                
                if matches:
                    # Get best match (highest confidence)
                    best_match = max(matches, key=lambda m: m[4])
                    confidence = best_match[4]
                    
                    logger.info(f"Target found with confidence: {confidence:.2f}")
                    
                    # Move cursor to target
                    cursor_controller.move_to_target(best_match)
                    
                    # For this example, we'll exit after finding the target
                    # In a real application, you might want to keep running
                    break
                else:
                    logger.info("Target not found in current frame")
                
                # Sleep to avoid high CPU usage
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        
        # Save targets before exiting
        target_manager.save_targets()
        
    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)

if __name__ == "__main__":
    main()