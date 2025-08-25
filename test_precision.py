import cv2
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from precise_tracking import PrecisePeopleTracker

def test_precise_detection():
    """Test the new precise people detection system"""
    print("🎯 Testing Precision People Detection System")
    print("=" * 50)
    
    # Initialize tracker with strict settings
    tracker = PrecisePeopleTracker(conf_threshold=0.5)
    
    # Test with camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible!")
        return False
    
    print("✓ Camera opened successfully")
    print("🎯 Precision Detection Active:")
    print("   - Multi-method validation (HOG + Face + Motion)")
    print("   - Strict aspect ratio: 2.0 - 4.0")
    print("   - Minimum size: 40x100 pixels")
    print("   - Validation score required: ≥ 1.2")
    print("")
    print("📹 Live Detection Test:")
    print("Press 'q' to quit, 's' to start/stop tracking")
    print("=" * 50)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process every frame for testing
        if tracker.is_tracking:
            # Test detection
            detections = tracker.detect_people(frame)
            
            # Process frame with tracking
            processed_frame = tracker.process_frame(frame)
            
            # Show detection info every 30 frames
            if frame_count % 30 == 0:
                print(f"Frame {frame_count}: {len(detections)} validated people detected")
            
            cv2.imshow('Precision People Detection', processed_frame)
        else:
            # Show original frame when not tracking
            cv2.putText(frame, "Press 's' to start precision tracking", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow('Precision People Detection', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            if tracker.is_tracking:
                tracker.stop_tracking()
                print("🛑 Tracking stopped")
            else:
                tracker.start_tracking()
                print("🎯 Precision tracking started")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test completed!")

if __name__ == "__main__":
    test_precise_detection()
