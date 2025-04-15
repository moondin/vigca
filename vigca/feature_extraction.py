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
        if method not in self.METHODS:
            method = "template_matching"
            logger.warning(f"Unknown method '{method}', defaulting to template_matching")
        
        self.method = method
        self.threshold = 0.8  # Default confidence threshold
        
        # Initialize feature detection algorithm for feature matching
        if self.method == "feature_matching":
            # Use ORB as it's available in the standard OpenCV package
            self.feature_detector = cv2.ORB_create()
        
        logger.debug(f"Feature extractor initialized with method: {method}")
    
    def set_method(self, method):
        """
        Change the feature extraction method.
        
        Args:
            method (str): The feature extraction method to use
        """
        if method not in self.METHODS:
            logger.warning(f"Unknown method '{method}', keeping current method")
            return
        
        self.method = method
        
        # Initialize feature detection algorithm if needed
        if self.method == "feature_matching":
            self.feature_detector = cv2.ORB_create()
        
        logger.debug(f"Feature extraction method set to: {method}")
    
    def set_threshold(self, threshold):
        """
        Set the confidence threshold for feature matching.
        
        Args:
            threshold (float): The confidence threshold (0.0 to 1.0)
        """
        self.threshold = max(0.1, min(threshold, 1.0))  # Limit to valid range
        logger.debug(f"Confidence threshold set to: {threshold}")
    
    def extract_features(self, image):
        """
        Extract features from the given image based on the current method.
        
        Args:
            image (numpy.ndarray): The image to extract features from
            
        Returns:
            object: Method-specific feature representation
        """
        if image is None or image.size == 0:
            logger.warning("Cannot extract features from empty image")
            return None
        
        if self.method == "template_matching":
            # For template matching, the image itself is the feature
            return image
        
        elif self.method == "feature_matching":
            # Convert to grayscale if needed
            if len(image.shape) > 2 and image.shape[2] > 1:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Extract keypoints and descriptors
            keypoints, descriptors = self.feature_detector.detectAndCompute(gray, None)
            
            # Return as a dict with the original image, keypoints and descriptors
            return {
                "image": image,
                "keypoints": keypoints,
                "descriptors": descriptors
            }
        
        else:
            logger.error(f"Unknown feature extraction method: {self.method}")
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
        if target_features is None or screen_image is None:
            logger.warning("Cannot find matches with empty target features or screen image")
            return []
        
        if self.method == "template_matching":
            return self._find_matches_template(target_features, screen_image)
        
        elif self.method == "feature_matching":
            return self._find_matches_feature(target_features, screen_image)
        
        else:
            logger.error(f"Unknown matching method: {self.method}")
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
        # Convert images to grayscale if they have color channels
        if len(template.shape) > 2 and template.shape[2] > 1:
            template_gray = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        else:
            template_gray = template
        
        if len(screen_image.shape) > 2 and screen_image.shape[2] > 1:
            screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_RGB2GRAY)
        else:
            screen_gray = screen_image
        
        # Get template dimensions
        h, w = template_gray.shape
        
        # Check if template is larger than screen image
        if h > screen_gray.shape[0] or w > screen_gray.shape[1]:
            logger.warning("Template is larger than screen image, cannot match")
            return []
        
        # Apply template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Find all locations where the matching value exceeds the threshold
        locations = np.where(result >= self.threshold)
        matches = []
        
        # Convert to list of matches with confidence values
        for pt in zip(*locations[::-1]):  # Reverse because numpy uses (y, x) instead of (x, y)
            x, y = pt
            confidence = result[y, x]
            matches.append((x, y, w, h, confidence))
        
        # Apply non-maximum suppression to remove overlapping matches
        matches = self._non_max_suppression(matches)
        
        logger.debug(f"Found {len(matches)} template matches with threshold {self.threshold}")
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
        # Extract target data
        target_image = target_features["image"]
        target_keypoints = target_features["keypoints"]
        target_descriptors = target_features["descriptors"]
        
        # Check if we have enough features to match
        if target_descriptors is None or len(target_keypoints) < 4:
            logger.warning("Not enough features in target for matching")
            return []
        
        # Convert screen image to grayscale if needed
        if len(screen_image.shape) > 2 and screen_image.shape[2] > 1:
            screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_RGB2GRAY)
        else:
            screen_gray = screen_image
        
        # Extract features from screen image
        screen_keypoints, screen_descriptors = self.feature_detector.detectAndCompute(screen_gray, None)
        
        if screen_descriptors is None or len(screen_keypoints) < 4:
            logger.warning("Not enough features in screen image for matching")
            return []
        
        # Create matcher
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Find matches
        matches = matcher.match(target_descriptors, screen_descriptors)
        
        # Sort matches by distance (lower is better)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Get target dimensions
        h, w = target_image.shape[:2]
        
        # We need at least 10 good matches to consider it a positive detection
        min_good_matches = 10
        
        if len(matches) < min_good_matches:
            return []
        
        # Use only the top matches
        good_matches = matches[:min(50, len(matches))]
        
        # Extract locations of good matches
        target_pts = np.float32([target_keypoints[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        screen_pts = np.float32([screen_keypoints[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # Calculate homography to find the object location
        H, mask = cv2.findHomography(target_pts, screen_pts, cv2.RANSAC, 5.0)
        
        if H is None:
            return []
        
        # Apply homography to get the corners of the target in the screen image
        h, w = target_image.shape[:2]
        target_corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
        screen_corners = cv2.perspectiveTransform(target_corners, H)
        
        # Convert to int and get bounding box
        screen_corners = np.int32(screen_corners)
        x, y, w, h = cv2.boundingRect(screen_corners)
        
        # Calculate confidence based on number of inliers
        inliers = np.sum(mask)
        confidence = min(1.0, inliers / min_good_matches)
        
        # Only return match if confidence is high enough
        if confidence >= self.threshold:
            logger.debug(f"Found feature match with confidence {confidence:.2f}")
            return [(x, y, w, h, confidence)]
        else:
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
        if len(matches) == 0:
            return []
        
        # Sort by confidence (descending)
        matches = sorted(matches, key=lambda x: x[4], reverse=True)
        
        # List to hold final matches after non-max suppression
        keep = []
        
        while len(matches) > 0:
            # Take the match with highest confidence and add to keep list
            best_match = matches[0]
            keep.append(best_match)
            
            # Remove matches with high overlap
            remaining_matches = []
            best_x, best_y, best_w, best_h, _ = best_match
            best_area = best_w * best_h
            
            for match in matches[1:]:
                x, y, w, h, _ = match
                
                # Calculate intersection area
                xx1 = max(best_x, x)
                yy1 = max(best_y, y)
                xx2 = min(best_x + best_w, x + w)
                yy2 = min(best_y + best_h, y + h)
                
                intersection_w = max(0, xx2 - xx1)
                intersection_h = max(0, yy2 - yy1)
                intersection_area = intersection_w * intersection_h
                
                # Calculate union area
                match_area = w * h
                union_area = best_area + match_area - intersection_area
                
                # Calculate overlap ratio
                overlap = intersection_area / float(union_area)
                
                # Keep matches with low overlap
                if overlap <= overlap_threshold:
                    remaining_matches.append(match)
            
            matches = remaining_matches
        
        return keep