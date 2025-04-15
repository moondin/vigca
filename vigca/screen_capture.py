"""
Screen Capture Module for ViGCA

Provides functionality for capturing screenshots of the user's screen
at a configurable rate.
"""
import time
import numpy as np
import cv2
import mss
import mss.tools
import logging

logger = logging.getLogger(__name__)

class ScreenCapture:
    """
    Handles screen capturing functionality with configurable parameters.
    """
    
    def __init__(self, capture_rate=1.0, roi=None):
        """
        Initialize the screen capture module.
        
        Args:
            capture_rate (float): Screenshots per second
            roi (tuple): Region of interest (left, top, width, height) or None for full screen
        """
        self.capture_rate = max(0.1, min(capture_rate, 30.0))  # Limit to reasonable range
        self.interval = 1.0 / self.capture_rate
        self.roi = roi
        self.last_capture_time = 0
        self.last_frame = None
        self.sct = mss.mss()
        
        # Get primary monitor dimensions
        self.monitor = self.sct.monitors[1]  # Primary monitor
        
        logger.debug(f"Screen capture initialized with rate: {capture_rate} fps, interval: {self.interval} sec")
        if roi:
            logger.debug(f"Using ROI: {roi}")
        else:
            logger.debug(f"Using full screen: {self.monitor}")
    
    def set_capture_rate(self, rate):
        """
        Update the capture rate.
        
        Args:
            rate (float): New capture rate in frames per second
        """
        self.capture_rate = max(0.1, min(rate, 30.0))  # Limit to reasonable range
        self.interval = 1.0 / self.capture_rate
        logger.debug(f"Capture rate set to: {self.capture_rate} fps, interval: {self.interval} sec")
    
    def set_roi(self, roi=None):
        """
        Set a new region of interest for screen captures.
        
        Args:
            roi (tuple): Region of interest as (left, top, width, height) or None for full screen
        """
        self.roi = roi
        if roi:
            logger.debug(f"ROI set to: {roi}")
        else:
            logger.debug("ROI cleared, using full screen")
    
    def get_roi_dimensions(self):
        """
        Get the dimensions of the current capture region.
        
        Returns:
            tuple: (width, height) of the capture region
        """
        if self.roi:
            return self.roi[2], self.roi[3]
        else:
            return self.monitor["width"], self.monitor["height"]
    
    def get_monitor_dimensions(self):
        """
        Get the dimensions of the primary monitor.
        
        Returns:
            tuple: (width, height) of the primary monitor
        """
        return self.monitor["width"], self.monitor["height"]
    
    def capture(self, force=False):
        """
        Capture a screenshot if enough time has passed since the last capture.
        
        Args:
            force (bool): If True, capture regardless of timing
            
        Returns:
            numpy.ndarray: The captured frame as an RGB image array or None if no capture was made
        """
        current_time = time.time()
        
        # Check if it's time for a new capture or if forced
        if force or (current_time - self.last_capture_time >= self.interval):
            try:
                # Define the capture region
                if self.roi:
                    left, top, width, height = self.roi
                    region = {"left": left, "top": top, "width": width, "height": height}
                else:
                    region = self.monitor
                
                # Grab the screenshot
                screenshot = self.sct.grab(region)
                
                # Convert to numpy array
                frame = np.array(screenshot)
                
                # Convert from BGRA to RGB (OpenCV format)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                
                # Update last capture time and frame
                self.last_capture_time = current_time
                self.last_frame = frame
                
                return frame
                
            except Exception as e:
                logger.error(f"Error capturing screen: {e}", exc_info=True)
                return None
        else:
            return None
    
    def get_last_frame(self):
        """
        Get the most recently captured frame.
        
        Returns:
            numpy.ndarray: The last captured frame or None if no frame has been captured
        """
        return self.last_frame