import cv2
import numpy as np
import json
import uuid
from datetime import datetime
import sqlite3
import os

class SimpleDB:
    """Simple SQLite database wrapper"""
    
    def __init__(self, db_path="people_tracking.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_people_count INTEGER DEFAULT 0,
                current_people_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                x REAL NOT NULL,
                y REAL NOT NULL,
                width REAL NOT NULL,
                height REAL NOT NULL,
                confidence REAL NOT NULL,
                session_id TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def add_session(self, session_id):
        """Add a new tracking session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tracking_sessions (session_id) VALUES (?)",
            (session_id,)
        )
        conn.commit()
        conn.close()
    
    def update_session_stats(self, session_id, current_count, total_count):
        """Update session statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tracking_sessions SET current_people_count = ?, total_people_count = ? WHERE session_id = ?",
            (current_count, total_count, session_id)
        )
        conn.commit()
        conn.close()
    
    def stop_session(self, session_id):
        """Stop a tracking session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tracking_sessions SET status = 'stopped', end_time = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
    
    def add_person_detection(self, track_id, x, y, width, height, confidence, session_id):
        """Add a person detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO persons (track_id, x, y, width, height, confidence, session_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (track_id, x, y, width, height, confidence, session_id)
        )
        conn.commit()
        conn.close()
    
    def get_session_stats(self, session_id):
        """Get session statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tracking_sessions WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'session_id': result[1],
                'start_time': result[2],
                'end_time': result[3],
                'total_people': result[4],
                'current_people': result[5],
                'status': result[6]
            }
        return None

class PrecisePeopleTracker:
    def __init__(self, conf_threshold=0.5):
        """Initialize the precise people tracker with multiple detection methods"""
        
        # Initialize multiple detectors for better accuracy
        self._init_detectors()
        
        self.conf_threshold = conf_threshold
        self.session_id = str(uuid.uuid4())
        self.current_tracks = {}
        self.people_count = 0
        self.total_people_count = 0
        self.is_tracking = False
        self.track_id_counter = 1
        
        # Simple tracking parameters
        self.track_threshold = 50  # Pixel distance threshold for tracking
        
        # Strict people detection parameters for precision
        self.min_person_width = 40      # Minimum width in pixels
        self.min_person_height = 100    # Minimum height in pixels (much stricter)
        self.max_person_width = 300     # Maximum width in pixels
        self.max_person_height = 500    # Maximum height in pixels
        self.min_aspect_ratio = 2.0     # Much stricter - people are at least 2x taller than wide
        self.max_aspect_ratio = 4.0     # Maximum height/width ratio
        
        # Multi-method validation
        self.min_detectors_agree = 1    # At least 1 detector must agree
        
        # Initialize database
        self.db = SimpleDB()
        self.db.add_session(self.session_id)
        print(f"Created tracking session: {self.session_id}")
        print(f"Precision People Detection System Initialized")
        print(f"- HOG + Face cascade + Motion detection")
        print(f"- Strict filtering: AR >= 2.0, size >= 40x100")
        print(f"- Confidence threshold: {self.conf_threshold}")
    
    def _init_detectors(self):
        """Initialize multiple detection methods"""
        # 1. HOG People Detector (primary)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # 2. Haar Cascade for face detection (secondary validation)
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.face_detection_enabled = True
            print("✓ Face detection enabled")
        except:
            self.face_detection_enabled = False
            print("⚠ Face detection not available")
        
        # 3. Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # 4. Previous frame for temporal consistency
        self.prev_frame = None
    
    def detect_people(self, frame):
        """Detect people using multiple methods with strict validation"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Method 1: HOG Detection (primary)
        hog_detections = self._hog_detection(frame)
        
        # Method 2: Face validation (secondary)
        face_regions = self._detect_faces(gray) if self.face_detection_enabled else []
        
        # Method 3: Motion analysis
        motion_regions = self._detect_motion(frame)
        
        # Combine and validate detections
        validated_detections = self._validate_detections(hog_detections, face_regions, motion_regions, frame)
        
        # Update previous frame
        self.prev_frame = gray.copy()
        
        return validated_detections
    
    def _hog_detection(self, frame):
        """HOG people detection with strict parameters"""
        # More conservative HOG detection
        boxes, weights = self.hog.detectMultiScale(frame, 
                                                  winStride=(8, 8),     # Larger stride for stability
                                                  padding=(32, 32),     # More padding
                                                  scale=1.05,           # Larger scale step
                                                  groupThreshold=2)     # Require group consensus
        
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            confidence = float(weights[i])
            
            if confidence > self.conf_threshold:
                aspect_ratio = h / w if w > 0 else 0
                
                # Much stricter filtering
                if (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio and
                    self.min_person_width <= w <= self.max_person_width and 
                    self.min_person_height <= h <= self.max_person_height):
                    
                    detections.append({
                        'bbox': [x, y, w, h],
                        'confidence': confidence,
                        'center': [x + w//2, y + h//2],
                        'aspect_ratio': aspect_ratio,
                        'method': 'HOG'
                    })
        
        return detections
    
    def _detect_faces(self, gray):
        """Detect faces to validate person detections"""
        if not self.face_detection_enabled:
            return []
        
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        return [{'bbox': [x, y, w, h], 'center': [x + w//2, y + h//2]} for x, y, w, h in faces]
    
    def _detect_motion(self, frame):
        """Detect motion regions that might contain people"""
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_regions = []
        for contour in contours:
            if cv2.contourArea(contour) > 1000:  # Minimum area for person
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                # Check if it could be a person
                if (aspect_ratio > 1.5 and 
                    w > 30 and h > 60):
                    motion_regions.append({
                        'bbox': [x, y, w, h],
                        'center': [x + w//2, y + h//2]
                    })
        
        return motion_regions
    
    def _validate_detections(self, hog_detections, face_regions, motion_regions, frame):
        """Validate detections using multiple methods"""
        validated = []
        
        for detection in hog_detections:
            bbox = detection['bbox']
            x, y, w, h = bbox
            center = detection['center']
            
            # Validation score
            validation_score = 1.0  # Start with HOG detection
            
            # Check for face in upper portion of detection
            face_found = False
            upper_region = [x, y, w, h//2]  # Upper half of detection
            
            for face in face_regions:
                face_center = face['center']
                if (upper_region[0] <= face_center[0] <= upper_region[0] + upper_region[2] and
                    upper_region[1] <= face_center[1] <= upper_region[1] + upper_region[3]):
                    face_found = True
                    validation_score += 0.5
                    break
            
            # Check for motion correlation
            motion_found = False
            for motion in motion_regions:
                motion_center = motion['center']
                distance = np.sqrt((center[0] - motion_center[0])**2 + (center[1] - motion_center[1])**2)
                if distance < 50:  # Within 50 pixels
                    motion_found = True
                    validation_score += 0.3
                    break
            
            # Additional validation: check if it's actually person-like
            roi = frame[y:y+h, x:x+w]
            if roi.size > 0:
                # Check color distribution (people usually have varied colors)
                hist = cv2.calcHist([roi], [0, 1, 2], None, [16, 16, 16], [0, 256, 0, 256, 0, 256])
                color_variance = np.std(hist)
                
                if color_variance > 50:  # Good color variation
                    validation_score += 0.2
                
                # Check for vertical edges (people have clothing edges, etc.)
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray_roi, 50, 150)
                vertical_edges = np.sum(edges[:, :] > 0)
                
                if vertical_edges > (w * h * 0.1):  # At least 10% edge pixels
                    validation_score += 0.2
            
            # Apply strict validation threshold
            if validation_score >= 1.2:  # Require some additional validation beyond just HOG
                detection['validation_score'] = validation_score
                detection['face_detected'] = face_found
                detection['motion_detected'] = motion_found
                validated.append(detection)
                
                print(f"✓ Valid person: conf={detection['confidence']:.2f}, AR={detection['aspect_ratio']:.1f}, "
                      f"score={validation_score:.1f}, face={face_found}, motion={motion_found}")
            else:
                print(f"✗ Rejected: conf={detection['confidence']:.2f}, AR={detection['aspect_ratio']:.1f}, "
                      f"score={validation_score:.1f} (insufficient validation)")
        
        return validated
    
    def simple_tracking(self, detections):
        """Simple tracking based on proximity"""
        new_tracks = {}
        used_track_ids = set()
        
        for detection in detections:
            center = detection['center']
            best_match = None
            min_distance = float('inf')
            
            # Find closest existing track
            for track_id, track_info in self.current_tracks.items():
                if track_id in used_track_ids:
                    continue
                    
                track_center = track_info['center']
                distance = np.sqrt((center[0] - track_center[0])**2 + 
                                 (center[1] - track_center[1])**2)
                
                if distance < self.track_threshold and distance < min_distance:
                    min_distance = distance
                    best_match = track_id
            
            if best_match:
                # Update existing track
                new_tracks[best_match] = {
                    'bbox': detection['bbox'],
                    'center': center,
                    'confidence': detection['confidence'],
                    'validation_score': detection['validation_score'],
                    'age': self.current_tracks[best_match]['age'] + 1
                }
                used_track_ids.add(best_match)
            else:
                # Create new track
                new_tracks[self.track_id_counter] = {
                    'bbox': detection['bbox'],
                    'center': center,
                    'confidence': detection['confidence'],
                    'validation_score': detection['validation_score'],
                    'age': 1
                }
                self.track_id_counter += 1
        
        return new_tracks
    
    def process_frame(self, frame):
        """Process a single frame for tracking"""
        if not self.is_tracking:
            return frame
        
        # Detect people with multiple validation
        detections = self.detect_people(frame)
        
        # Update tracks
        new_tracks = self.simple_tracking(detections)
        
        # Count new people
        new_people = len(new_tracks) - len(self.current_tracks)
        if new_people > 0:
            self.total_people_count += new_people
        
        self.current_tracks = new_tracks
        self.people_count = len(self.current_tracks)
        
        # Draw bounding boxes and labels
        for track_id, track_info in self.current_tracks.items():
            x, y, w, h = track_info['bbox']
            confidence = track_info['confidence']
            validation_score = track_info.get('validation_score', 0)
            
            # Store tracking data
            try:
                self.db.add_person_detection(track_id, x, y, w, h, confidence, self.session_id)
            except Exception as e:
                print(f"Error storing data: {e}")
            
            # Draw bounding box with validation-based color
            color = (0, 255, 0) if validation_score > 1.5 else (0, 200, 100)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label with validation info
            label = f"Person {track_id} ({confidence:.2f}|{validation_score:.1f})"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Update session statistics
        try:
            self.db.update_session_stats(self.session_id, self.people_count, self.total_people_count)
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        # Add count overlay
        cv2.putText(frame, f"Validated People: {self.people_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Total Detected: {self.total_people_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame
    
    def start_tracking(self):
        """Start tracking"""
        self.is_tracking = True
        print("Precision people tracking started")
    
    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        try:
            self.db.stop_session(self.session_id)
        except Exception as e:
            print(f"Error stopping session: {e}")
        print("Tracking stopped")
    
    def get_stats(self):
        """Get current statistics"""
        return {
            'current_people': self.people_count,
            'total_people': self.total_people_count,
            'is_tracking': self.is_tracking,
            'session_id': self.session_id,
            'status': 'active' if self.is_tracking else 'inactive'
        }

class VideoStream:
    """Video streaming class for Flask"""
    def __init__(self, source=0):
        self.capture = cv2.VideoCapture(source)
        self.tracker = None
        self.running = False
    
    def set_tracker(self, tracker):
        """Set the people tracker"""
        self.tracker = tracker
    
    def get_frame(self):
        """Get processed frame"""
        ret, frame = self.capture.read()
        if ret and self.tracker:
            frame = self.tracker.process_frame(frame)
        return ret, frame
    
    def start(self):
        """Start video stream"""
        self.running = True
    
    def stop(self):
        """Stop video stream"""
        self.running = False
        if self.capture:
            self.capture.release()
