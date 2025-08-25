#!/usr/bin/env python3
"""
Test script to verify all dependencies are installed correctly
"""

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics YOLO imported successfully")
    except ImportError as e:
        print(f"✗ Ultralytics import failed: {e}")
        return False
    
    try:
        from deep_sort_realtime import DeepSort
        print("✓ DeepSORT imported successfully")
    except ImportError as e:
        print(f"✗ DeepSORT import failed: {e}")
        return False
    
    try:
        # Face recognition is optional for now
        print("✓ Face recognition (optional - placeholder implementation)")
    except ImportError as e:
        print(f"! Face recognition not available (optional): {e}")
    
    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        from flask_sqlalchemy import SQLAlchemy
        print("✓ Flask-SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"✗ Flask-SQLAlchemy import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera access"""
    print("\nTesting camera access...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✓ Camera access successful")
                print(f"  Frame shape: {frame.shape}")
            else:
                print("✗ Camera opened but no frame captured")
            cap.release()
            return True
        else:
            print("✗ Camera could not be opened")
            return False
            
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

def test_yolo_model():
    """Test YOLO model loading"""
    print("\nTesting YOLO model...")
    
    try:
        from ultralytics import YOLO
        
        # This will download the model if not present
        model = YOLO('yolov8n.pt')
        print("✓ YOLOv8 model loaded successfully")
        print(f"  Model path: {model.model_path if hasattr(model, 'model_path') else 'yolov8n.pt'}")
        return True
        
    except Exception as e:
        print(f"✗ YOLO model test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("FaceScannerPro - Dependency Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test camera
    if test_camera():
        tests_passed += 1
    
    # Test YOLO model
    if test_yolo_model():
        tests_passed += 1
    
    print(f"\nTest Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Your environment is ready.")
        print("\nTo start the application, run:")
        print("  python app.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("- Ensure all packages are installed: pip install -r requirements.txt")
        print("- Check camera permissions and connections")
        print("- Ensure stable internet connection for model download")

if __name__ == "__main__":
    main()
