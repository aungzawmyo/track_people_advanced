import cv2
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minimal_tracking import MinimalPeopleTracker

def test_improved_detection():
    """Test the improved people detection"""
    print("Testing improved people detection...")
    
    # Initialize tracker with new settings
    tracker = MinimalPeopleTracker(conf_threshold=0.3)
    
    # Test with camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible!")
        return False
    
    print("✓ Camera opened, testing detection...")
    print("Press 'q' to quit, 's' to start/stop tracking")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Test detection
        detections = tracker.detect_people(frame)
        print(f"Found {len(detections)} people detections")
        
        # Draw detections
        for detection in detections:
            x, y, w, h = detection['bbox']
            conf = detection['confidence']
            ar = detection['aspect_ratio']
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"Person ({conf:.2f}) AR:{ar:.1f}"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add info overlay
        cv2.putText(frame, f"Detections: {len(detections)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('People Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed!")

if __name__ == "__main__":
    test_improved_detection()
