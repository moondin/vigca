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
        self.capture_rate = capture_rate
        self.roi = roi
        self.last_capture_time = 0
        self.current_frame = None
        self.sct = mss.mss()
        
        # Get the default monitor dimensions
        self.monitors = self.sct.monitors
        self.primary_monitor = self.monitors[1]  # Primary monitor is usually at index 1
        
        logger.debug(f"Screen capture initialized with rate: {capture_rate} fps")
        logger.debug(f"Primary monitor dimensions: {self.primary_monitor}")
    
    def set_capture_rate(self, rate):
        """
        Update the capture rate.
        
        Args:
            rate (float): New capture rate in frames per second
        """
        self.capture_rate = max(0.1, min(rate, 30.0))  # Limit to reasonable range
        logger.debug(f"Capture rate updated to {self.capture_rate} fps")
    
    def set_roi(self, roi=None):
        """
        Set a new region of interest for screen captures.
        
        Args:
            roi (tuple): Region of interest as (left, top, width, height) or None for full screen
        """
        self.roi = roi
        logger.debug(f"Region of interest updated: {roi}")
    
    def get_roi_dimensions(self):
        """
        Get the dimensions of the current capture region.
        
        Returns:
            tuple: (width, height) of the capture region
        """
        if self.roi:
            return (self.roi[2], self.roi[3])
        else:
            return (self.primary_monitor["width"], self.primary_monitor["height"])
    
    def get_monitor_dimensions(self):
        """
        Get the dimensions of the primary monitor.
        
        Returns:
            tuple: (width, height) of the primary monitor
        """
        return (self.primary_monitor["width"], self.primary_monitor["height"])
    
    def capture(self, force=False):
        """
        Capture a screenshot if enough time has passed since the last capture.
        
        Args:
            force (bool): If True, capture regardless of timing
            
        Returns:
            numpy.ndarray: The captured frame as an RGB image array or None if no capture was made
        """
        current_time = time.time()
        time_since_last = current_time - self.last_capture_time
        
        # Only capture if enough time has passed or we're forcing a capture
        if force or time_since_last >= 1.0 / self.capture_rate:
            try:
                # Define the capture region
                if self.roi:
                    monitor = {
                        "left": self.roi[0],
                        "top": self.roi[1],
                        "width": self.roi[2],
                        "height": self.roi[3]
                    }
                else:
                    monitor = self.primary_monitor
                
                # Capture the screenshot
                sct_img = self.sct.grab(monitor)
                
                # Convert to a numpy array
                img = np.array(sct_img)
                
                # Convert from BGRA to RGB
                self.current_frame = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                
                self.last_capture_time = current_time
                return self.current_frame
            
            except Exception as e:
                logger.error(f"Error capturing screen: {e}", exc_info=True)
                return None
        else:
            return self.current_frame  # Return the last frame if no new capture
    
    def get_last_frame(self):
        """
        Get the most recently captured frame.
        
        Returns:
            numpy.ndarray: The last captured frame or None if no frame has been captured
        """
        return self.current_frame
