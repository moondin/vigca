"""
Cursor Control Module for ViGCA

Provides functionality for moving the mouse cursor to detected targets.
"""
import time
import pyautogui
import logging

# Disable PyAutoGUI fail-safe (comment out if you want to keep it as a safety feature)
pyautogui.FAILSAFE = False

logger = logging.getLogger(__name__)

class CursorController:
    """
    Controls the movement of the mouse cursor based on detected targets.
    """
    
    def __init__(self, speed=5.0, smooth=True):
        """
        Initialize the cursor controller.
        
        Args:
            speed (float): Movement speed (1.0 is slow, 10.0 is fast)
            smooth (bool): Whether to use smooth movements
        """
        self.speed = speed
        self.smooth = smooth
        self.screen_width, self.screen_height = pyautogui.size()
        logger.debug(f"Cursor controller initialized with speed: {speed}, smooth: {smooth}")
        logger.debug(f"Screen dimensions: {self.screen_width}x{self.screen_height}")
    
    def set_speed(self, speed):
        """
        Set the cursor movement speed.
        
        Args:
            speed (float): New speed value (1.0 to 10.0)
        """
        self.speed = max(1.0, min(speed, 10.0))  # Limit to reasonable range
        logger.debug(f"Cursor speed set to: {self.speed}")
    
    def set_smooth(self, smooth):
        """
        Set whether cursor movement should be smooth.
        
        Args:
            smooth (bool): Whether to use smooth movements
        """
        self.smooth = bool(smooth)
        logger.debug(f"Smooth cursor movement set to: {self.smooth}")
    
    def move_to(self, x, y):
        """
        Move the cursor to the specified coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            
        Returns:
            bool: True if movement was successful, False otherwise
        """
        try:
            # Ensure coordinates are within screen bounds
            x = max(0, min(x, self.screen_width - 1))
            y = max(0, min(y, self.screen_height - 1))
            
            # Get current position
            current_x, current_y = pyautogui.position()
            
            if self.smooth:
                # Calculate duration based on distance and speed
                distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
                duration = distance / (200.0 * self.speed)  # Adjust constant for desired feel
                duration = max(0.1, min(duration, 2.0))  # Limit to reasonable range
                
                # Move cursor smoothly
                pyautogui.moveTo(x, y, duration=duration)
            else:
                # Move cursor instantly
                pyautogui.moveTo(x, y)
            
            logger.debug(f"Moved cursor to ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"Error moving cursor: {e}", exc_info=True)
            return False
    
    def move_to_target(self, target_box):
        """
        Move the cursor to the center of a detected target.
        
        Args:
            target_box (tuple): (x, y, width, height, confidence) of the target
            
        Returns:
            bool: True if movement was successful, False otherwise
        """
        try:
            x, y, width, height, confidence = target_box
            
            # Calculate center point
            center_x = x + width // 2
            center_y = y + height // 2
            
            # Move to center of target
            return self.move_to(center_x, center_y)
            
        except Exception as e:
            logger.error(f"Error moving to target: {e}", exc_info=True)
            return False
    
    def click(self, button='left'):
        """
        Perform a mouse click at the current position.
        
        Args:
            button (str): Mouse button to click ('left', 'right', 'middle')
            
        Returns:
            bool: True if click was successful, False otherwise
        """
        try:
            pyautogui.click(button=button)
            logger.debug(f"Clicked {button} button")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking: {e}", exc_info=True)
            return False
