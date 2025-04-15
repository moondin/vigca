"""
Configuration Module for ViGCA

Handles application settings and configuration.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

class Configuration:
    """
    Manages application settings and provides persistence.
    """
    
    DEFAULT_CONFIG = {
        "screen_capture": {
            "capture_rate": 1.0,  # Frames per second
            "use_roi": False,     # Whether to use a region of interest
            "roi": [0, 0, 800, 600]  # Default ROI (x, y, width, height)
        },
        "feature_extraction": {
            "method": "template_matching",  # Default feature extraction method
            "threshold": 0.8  # Default confidence threshold
        },
        "cursor_control": {
            "speed": 5.0,  # Movement speed
            "smooth": True  # Whether to use smooth movements
        },
        "application": {
            "auto_start": False,  # Whether to start detection automatically
            "ui_theme": "dark",   # UI theme
            "active_target_ids": []  # IDs of targets that are currently active
        }
    }
    
    def __init__(self, config_file="vigca_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
        logger.debug(f"Configuration initialized from: {config_file}")
    
    def get(self, section, key=None):
        """
        Get a configuration value.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key (or None to get entire section)
            
        Returns:
            object: Configuration value or section dict
        """
        if section not in self.config:
            logger.warning(f"Section '{section}' not found in configuration")
            return None
        
        if key is None:
            return self.config[section]
        
        if key not in self.config[section]:
            logger.warning(f"Key '{key}' not found in section '{section}'")
            return None
        
        return self.config[section][key]
    
    def set(self, section, key, value):
        """
        Set a configuration value.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            value (object): Configuration value
            
        Returns:
            bool: True if set was successful, False otherwise
        """
        if section not in self.config:
            logger.warning(f"Section '{section}' not found in configuration")
            return False
        
        self.config[section][key] = value
        logger.debug(f"Set configuration {section}.{key} = {value}")
        return True
    
    def save_config(self):
        """
        Save the configuration to file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.debug(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def load_config(self):
        """
        Load the configuration from file.
        
        Returns:
            bool: True if load was successful, False otherwise
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Update configuration, preserving default values for missing items
                for section in self.config:
                    if section in loaded_config:
                        for key in self.config[section]:
                            if key in loaded_config[section]:
                                self.config[section][key] = loaded_config[section][key]
                
                logger.debug(f"Loaded configuration from {self.config_file}")
                return True
            else:
                logger.debug(f"No configuration file found at {self.config_file}, using defaults")
                return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            return False
    
    def reset_to_defaults(self):
        """
        Reset configuration to default values.
        
        Returns:
            bool: True if reset was successful
        """
        self.config = self.DEFAULT_CONFIG.copy()
        logger.debug("Reset configuration to defaults")
        return True
