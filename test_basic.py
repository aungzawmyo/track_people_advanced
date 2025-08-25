#!/usr/bin/env python3
"""
Simplified test script to verify basic dependencies
"""

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
        print(f"  OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
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
        print(f"  NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    return True

def test_opencv_features():
    """Test OpenCV features needed for tracking"""
    print("\nTesting OpenCV features...")
    
    try:
        import cv2
        
        # Test HOG descriptor
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        print("✓ HOG people detector initialized")
        
        # Test cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("✓ Face cascade classifier loaded")
        
        return True
        
    except Exception as e:
        print(f"✗ OpenCV features test failed: {e}")
        return False

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

def main():
    """Run all tests"""
    print("FaceScannerPro - Basic Setup Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    # Test basic imports
    if test_basic_imports():
        tests_passed += 1
    
    # Test OpenCV features
    if test_opencv_features():
        tests_passed += 1
    
    # Test camera
    if test_camera():
        tests_passed += 1
    
    print(f"\nTest Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Your environment is ready.")
        print("\nTo start the application, run:")
        print("  python app.py")
        print("\nNote: This version uses OpenCV HOG detector instead of YOLO.")
        print("YOLO can be added later when disk space is available.")
    else:
        print("✗ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
