"""
Target Manager Module for ViGCA

Manages the storage, loading, and organization of visual targets
that the user has trained the system to recognize.
"""
import os
import pickle
import uuid
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class Target:
    """
    Represents a visual target that can be detected on the screen.
    """
    
    def __init__(self, name, features, features_method, bounding_box, image):
        """
        Initialize a new target.
        
        Args:
            name (str): Human-readable name for the target
            features (object): Extracted features for matching
            features_method (str): Method used for feature extraction
            bounding_box (tuple): (x, y, width, height) of the target in original image
            image (numpy.ndarray): Original image of the target
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.features = features
        self.features_method = features_method
        self.bounding_box = bounding_box
        self.image = image
        self.created_at = datetime.now()
        self.last_detected_at = None
        self.detection_count = 0
    
    def update_detection(self):
        """Update detection statistics when target is found."""
        self.last_detected_at = datetime.now()
        self.detection_count += 1


class TargetManager:
    """
    Manages a collection of visual targets and their persistence.
    """
    
    def __init__(self, storage_file="targets.pkl"):
        """
        Initialize the target manager.
        
        Args:
            storage_file (str): Path to the file where targets will be stored
        """
        self.storage_file = storage_file
        self.targets = {}
        self.load_targets()
        logger.debug(f"Target manager initialized with storage file: {storage_file}")
    
    def add_target(self, name, features, features_method, bounding_box, image):
        """
        Add a new target to the collection.
        
        Args:
            name (str): Human-readable name for the target
            features (object): Extracted features for matching
            features_method (str): Method used for feature extraction
            bounding_box (tuple): (x, y, width, height) of the target in original image
            image (numpy.ndarray): Original image of the target
            
        Returns:
            str: ID of the new target
        """
        target = Target(name, features, features_method, bounding_box, image)
        self.targets[target.id] = target
        self.save_targets()
        logger.info(f"Added new target: {name} (ID: {target.id})")
        return target.id
    
    def remove_target(self, target_id):
        """
        Remove a target from the collection.
        
        Args:
            target_id (str): ID of the target to remove
            
        Returns:
            bool: True if target was removed, False otherwise
        """
        if target_id in self.targets:
            name = self.targets[target_id].name
            del self.targets[target_id]
            self.save_targets()
            logger.info(f"Removed target: {name} (ID: {target_id})")
            return True
        return False
    
    def rename_target(self, target_id, new_name):
        """
        Rename a target.
        
        Args:
            target_id (str): ID of the target to rename
            new_name (str): New name for the target
            
        Returns:
            bool: True if target was renamed, False otherwise
        """
        if target_id in self.targets:
            old_name = self.targets[target_id].name
            self.targets[target_id].name = new_name
            self.save_targets()
            logger.info(f"Renamed target: {old_name} to {new_name} (ID: {target_id})")
            return True
        return False
    
    def get_target(self, target_id):
        """
        Get a target by its ID.
        
        Args:
            target_id (str): ID of the target to retrieve
            
        Returns:
            Target: The target object or None if not found
        """
        return self.targets.get(target_id)
    
    def get_all_targets(self):
        """
        Get all targets.
        
        Returns:
            dict: Dictionary of all targets with IDs as keys
        """
        return self.targets
    
    def save_targets(self):
        """
        Save all targets to the storage file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.storage_file, 'wb') as f:
                pickle.dump(self.targets, f)
            logger.debug(f"Saved {len(self.targets)} targets to {self.storage_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving targets: {e}", exc_info=True)
            return False
    
    def load_targets(self):
        """
        Load targets from the storage file.
        
        Returns:
            bool: True if load was successful, False otherwise
        """
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'rb') as f:
                    self.targets = pickle.load(f)
                logger.debug(f"Loaded {len(self.targets)} targets from {self.storage_file}")
                return True
            else:
                logger.debug(f"No target file found at {self.storage_file}, starting with empty collection")
                return False
        except Exception as e:
            logger.error(f"Error loading targets: {e}", exc_info=True)
            self.targets = {}
            return False
    
    def update_target_detection(self, target_id):
        """
        Update the detection statistics for a target.
        
        Args:
            target_id (str): ID of the detected target
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if target_id in self.targets:
            self.targets[target_id].update_detection()
            return True
        return False