import cv2
import numpy as np

def blur_face(image: np.ndarray) -> np.ndarray:
    """
    Detects faces in the image using OpenCV's built-in Haar Cascades 
    and applies a strong Gaussian blur to preserve privacy.
    Supports both frontal and profile face detections.
    If no face is detected, a fallback blur is applied to the upper head region.
    """
    if image is None or image.size == 0:
        return image
        
    img = image.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Load OpenCV's built-in Haar Cascades
    frontal_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    profile_cascade_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
    
    frontal_cascade = cv2.CascadeClassifier(frontal_cascade_path)
    profile_cascade = cv2.CascadeClassifier(profile_cascade_path)
    
    # Detect faces
    faces_front = frontal_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    faces_profile = profile_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
    
    # Combine detected bounding boxes
    all_faces = []
    if len(faces_front) > 0:
        all_faces.extend(faces_front)
    if len(faces_profile) > 0:
        all_faces.extend(faces_profile)
        
    if len(all_faces) == 0:
        # FALLBACK BLUR: If no face is detected by cascades, apply a blur to the upper center area
        # since it's a cropped person image resized to 640x640, the face is typically in this region.
        h, w = img.shape[:2]
        fallback_y1, fallback_y2 = int(h * 0.05), int(h * 0.35)
        fallback_x1, fallback_x2 = int(w * 0.25), int(w * 0.75)
        
        roi = img[fallback_y1:fallback_y2, fallback_x1:fallback_x2]
        # Apply extremely strong blur
        blurred_roi = cv2.GaussianBlur(roi, (99, 99), 30)
        img[fallback_y1:fallback_y2, fallback_x1:fallback_x2] = blurred_roi
        return img
        
    for (x, y, w, h) in all_faces:
        # Ensure coordinates are within image boundaries
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(img.shape[1], x + w)
        y_end = min(img.shape[0], y + h)
        
        if x_end > x_start and y_end > y_start:
            roi = img[y_start:y_end, x_start:x_end]
            # Kernel size must be positive and odd
            ksize = 99
            # Apply Gaussian Blur to the face region
            blurred_roi = cv2.GaussianBlur(roi, (ksize, ksize), 30)
            img[y_start:y_end, x_start:x_end] = blurred_roi
            
    return img
