#!/usr/bin/env python3
"""
Minimal test script to verify core dependencies
"""

def test_minimal_imports():
    """Test minimal imports for the application"""
    print("Testing minimal imports...")
    
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
        import numpy as np
        print("✓ NumPy imported successfully")
        print(f"  NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✓ SQLite3 imported successfully")
    except ImportError as e:
        print(f"✗ SQLite3 import failed: {e}")
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

def test_tracking_module():
    """Test the minimal tracking module"""
    print("\nTesting tracking module...")
    
    try:
        from minimal_tracking import MinimalPeopleTracker, VideoStream, SimpleDB
        print("✓ Minimal tracking module imported successfully")
        
        # Test database
        db = SimpleDB("test.db")
        print("✓ Database initialization successful")
        
        # Test tracker creation
        tracker = MinimalPeopleTracker()
        print("✓ People tracker created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Tracking module test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("FaceScannerPro - Minimal Setup Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 4
    
    # Test minimal imports
    if test_minimal_imports():
        tests_passed += 1
    
    # Test OpenCV features
    if test_opencv_features():
        tests_passed += 1
    
    # Test camera
    if test_camera():
        tests_passed += 1
    
    # Test tracking module
    if test_tracking_module():
        tests_passed += 1
    
    print(f"\nTest Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Your minimal environment is ready.")
        print("\nTo start the application, run:")
        print("  python minimal_app.py")
        print("\nFeatures available:")
        print("- OpenCV HOG people detection")
        print("- Simple tracking algorithm")
        print("- SQLite database storage")
        print("- Flask web interface with Tailwind CSS")
    else:
        print("✗ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
