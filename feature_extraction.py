"""
Visual Feature Extraction Module for ViGCA

Implements various methods to extract and match visual features 
from captured screen images.
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Handles feature extraction and matching for visual targets.
    """
    
    METHODS = {
        "template_matching": "Template Matching",
        "feature_matching": "Feature Matching"
    }
    
    def __init__(self, method="template_matching"):
        """
        Initialize the feature extractor with a specified method.
        
        Args:
            method (str): The feature extraction method to use
        """
        self.method = method
        self.threshold = 0.8  # Default confidence threshold
        logger.debug(f"Feature extractor initialized with method: {method}")
    
    def set_method(self, method):
        """
        Change the feature extraction method.
        
        Args:
            method (str): The feature extraction method to use
        """
        if method in self.METHODS:
            self.method = method
            logger.debug(f"Feature extraction method changed to: {method}")
        else:
            logger.warning(f"Unknown feature extraction method: {method}")
    
    def set_threshold(self, threshold):
        """
        Set the confidence threshold for feature matching.
        
        Args:
            threshold (float): The confidence threshold (0.0 to 1.0)
        """
        self.threshold = max(0.1, min(threshold, 1.0))  # Limit to valid range
        logger.debug(f"Confidence threshold set to: {self.threshold}")
    
    def extract_features(self, image):
        """
        Extract features from the given image based on the current method.
        
        Args:
            image (numpy.ndarray): The image to extract features from
            
        Returns:
            object: Method-specific feature representation
        """
        try:
            if self.method == "template_matching":
                # For template matching, we just return the image itself
                return image
            
            elif self.method == "feature_matching":
                # Convert to grayscale for feature detection
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                else:
                    gray = image
                
                # Create feature detector
                orb = cv2.ORB_create()
                
                # Detect keypoints and compute descriptors
                keypoints, descriptors = orb.detectAndCompute(gray, None)
                
                return {
                    "image": gray,
                    "keypoints": keypoints,
                    "descriptors": descriptors
                }
            
            else:
                logger.error(f"Unsupported feature extraction method: {self.method}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True)
            return None
    
    def find_matches(self, target_features, screen_image):
        """
        Find matches for the target in the screen image.
        
        Args:
            target_features (object): Features of the target
            screen_image (numpy.ndarray): Current screen image
            
        Returns:
            list: List of tuples (x, y, width, height, confidence) for each match
            that exceeds the threshold
        """
        try:
            if self.method == "template_matching":
                return self._find_matches_template(target_features, screen_image)
            
            elif self.method == "feature_matching":
                return self._find_matches_feature(target_features, screen_image)
            
            else:
                logger.error(f"Unsupported matching method: {self.method}")
                return []
                
        except Exception as e:
            logger.error(f"Error finding matches: {e}", exc_info=True)
            return []
    
    def _find_matches_template(self, template, screen_image):
        """
        Find matches using template matching.
        
        Args:
            template (numpy.ndarray): Template image
            screen_image (numpy.ndarray): Current screen image
            
        Returns:
            list: List of tuples (x, y, width, height, confidence)
        """
        # Ensure templates have the same number of channels
        if len(template.shape) == 3 and len(screen_image.shape) == 3:
            if template.shape[2] != screen_image.shape[2]:
                template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
                screen_image = cv2.cvtColor(screen_image, cv2.COLOR_RGB2GRAY)
        
        # Perform template matching
        result = cv2.matchTemplate(screen_image, template, cv2.TM_CCOEFF_NORMED)
        
        # Get the matches above threshold
        locations = np.where(result >= self.threshold)
        matches = []
        
        # Template dimensions
        h, w = template.shape[:2]
        
        # Convert to list of matches
        for pt in zip(*locations[::-1]):  # Switch columns and rows
            confidence = result[pt[1], pt[0]]
            matches.append((pt[0], pt[1], w, h, float(confidence)))
        
        # Apply non-maximum suppression to avoid multiple detections
        matches = self._non_max_suppression(matches)
        
        return matches
    
    def _find_matches_feature(self, target_features, screen_image):
        """
        Find matches using feature matching.
        
        Args:
            target_features (dict): Dict with 'image', 'keypoints', 'descriptors'
            screen_image (numpy.ndarray): Current screen image
            
        Returns:
            list: List of tuples (x, y, width, height, confidence)
        """
        # Extract features from the screen image
        if len(screen_image.shape) == 3:
            screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_RGB2GRAY)
        else:
            screen_gray = screen_image
        
        # Create feature detector and extractor
        orb = cv2.ORB_create()
        
        # Detect keypoints and compute descriptors
        screen_keypoints, screen_descriptors = orb.detectAndCompute(screen_gray, None)
        
        # Check if we found any keypoints or descriptors
        if screen_descriptors is None or target_features["descriptors"] is None:
            return []
        
        # Create feature matcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Match descriptors
        matches = bf.match(target_features["descriptors"], screen_descriptors)
        
        # Sort matches by distance (lower distance is better)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Filter matches by distance threshold
        # Normalize distances to 0-1 range (inverting so higher is better)
        if len(matches) > 0:
            max_dist = max(m.distance for m in matches)
            min_dist = min(m.distance for m in matches)
            dist_range = max(1.0, max_dist - min_dist)
            
            good_matches = []
            result_matches = []
            
            target_h, target_w = target_features["image"].shape[:2]
            
            for m in matches:
                # Calculate normalized confidence (higher is better)
                confidence = 1.0 - (m.distance - min_dist) / dist_range
                
                if confidence >= self.threshold:
                    good_matches.append(m)
                    
                    # Get the position
                    idx2 = m.trainIdx
                    screen_pt = screen_keypoints[idx2].pt
                    x, y = int(screen_pt[0]), int(screen_pt[1])
                    
                    # Approximate bounding box using the feature point as center
                    half_w, half_h = target_w // 2, target_h // 2
                    result_matches.append((x - half_w, y - half_h, target_w, target_h, confidence))
            
            # Apply non-maximum suppression to avoid multiple detections
            result_matches = self._non_max_suppression(result_matches)
            
            return result_matches
        
        return []
    
    def _non_max_suppression(self, matches, overlap_threshold=0.3):
        """
        Apply non-maximum suppression to avoid multiple detections of the same object.
        
        Args:
            matches (list): List of tuples (x, y, width, height, confidence)
            overlap_threshold (float): Maximum allowed overlap ratio
            
        Returns:
            list: Filtered list of matches
        """
        if not matches:
            return []
        
        # Convert to list of lists for easier manipulation
        boxes = [[x, y, x + w, y + h, conf] for (x, y, w, h, conf) in matches]
        boxes.sort(key=lambda x: x[4], reverse=True)
        
        keep = []
        
        while boxes:
            current = boxes.pop(0)
            keep.append(current)
            
            i = 0
            while i < len(boxes):
                # Calculate intersection
                ix1 = max(current[0], boxes[i][0])
                iy1 = max(current[1], boxes[i][1])
                ix2 = min(current[2], boxes[i][2])
                iy2 = min(current[3], boxes[i][3])
                
                iw = max(0, ix2 - ix1)
                ih = max(0, iy2 - iy1)
                
                # Intersection area
                intersection = iw * ih
                
                # Areas of both boxes
                box1_area = (current[2] - current[0]) * (current[3] - current[1])
                box2_area = (boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1])
                
                # Calculate overlap ratio with the smaller area
                overlap = intersection / min(box1_area, box2_area) if min(box1_area, box2_area) > 0 else 0
                
                if overlap > overlap_threshold:
                    boxes.pop(i)
                else:
                    i += 1
        
        # Convert back to original format
        result = [(box[0], box[1], box[2] - box[0], box[3] - box[1], box[4]) for box in keep]
        return result
