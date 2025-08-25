import cv2
import numpy as np

def test_camera():
    """Test camera access and basic detection"""
    print("Testing camera access...")
    
    # Test camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible!")
        return False
    
    print("✓ Camera opened successfully")
    
    # Test frame capture
    ret, frame = cap.read()
    if not ret:
        print("❌ Cannot read frame from camera!")
        cap.release()
        return False
    
    print(f"✓ Frame captured: {frame.shape}")
    
    # Test HOG detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Test detection on current frame
    boxes, weights = hog.detectMultiScale(frame, 
                                         winStride=(8, 8),
                                         padding=(32, 32),
                                         scale=1.05,
                                         groupThreshold=2)
    
    print(f"✓ HOG detector working. Found {len(boxes)} potential detections")
    
    if len(boxes) > 0:
        print("Detection details:")
        for i, (x, y, w, h) in enumerate(boxes):
            confidence = weights[i]
            aspect_ratio = h / w if w > 0 else 0
            print(f"  Detection {i+1}: ({x},{y},{w},{h}) conf={confidence:.2f} AR={aspect_ratio:.1f}")
    
    cap.release()
    return True

if __name__ == "__main__":
    test_camera()
