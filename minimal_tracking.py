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

class MinimalPeopleTracker:
    def __init__(self, conf_threshold=0.3):  # Lowered threshold for better detection
        """Initialize the people tracker with OpenCV HOG detector"""
        # Use OpenCV's HOG (Histogram of Oriented Gradients) people detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        self.conf_threshold = conf_threshold  # Balanced threshold for people detection
        self.session_id = str(uuid.uuid4())
        self.current_tracks = {}
        self.people_count = 0
        self.total_people_count = 0
        self.is_tracking = False
        self.track_id_counter = 1
        
        # Simple tracking parameters
        self.track_threshold = 50  # Pixel distance threshold for tracking
        
        # People detection filtering parameters
        self.min_person_width = 25      # Lowered minimum width in pixels
        self.min_person_height = 50     # Lowered minimum height in pixels
        self.max_person_width = 400     # Increased maximum width in pixels
        self.max_person_height = 600    # Increased maximum height in pixels
        self.min_aspect_ratio = 1.4     # Slightly lowered minimum height/width ratio
        self.max_aspect_ratio = 4.5     # Slightly increased maximum height/width ratio
        
        # Initialize database
        self.db = SimpleDB()
        self.db.add_session(self.session_id)
        print(f"Created tracking session: {self.session_id}")
        print(f"People detection threshold: {self.conf_threshold}")
        print(f"Filtering: Only detecting human-like shapes with proper proportions")
    
    def detect_people(self, frame):
        """Detect people in frame using HOG detector with improved filtering"""
        # Detect people with optimized parameters for better sensitivity
        boxes, weights = self.hog.detectMultiScale(frame, 
                                                  winStride=(4, 4),     # Smaller stride for better detection
                                                  padding=(16, 16),     # Reduced padding
                                                  scale=1.03,           # Smaller scale step
                                                  groupThreshold=1)     # Lower group threshold
        
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            confidence = float(weights[i])
            
            # Apply confidence threshold
            if confidence > self.conf_threshold:
                # Additional filtering based on aspect ratio (people are taller than wide)
                aspect_ratio = h / w if w > 0 else 0
                
                # People typically have aspect ratio between 1.4 and 4.5
                if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                    # Filter by size constraints
                    if (self.min_person_width <= w <= self.max_person_width and 
                        self.min_person_height <= h <= self.max_person_height):
                        
                        detections.append({
                            'bbox': [x, y, w, h],
                            'confidence': confidence,
                            'center': [x + w//2, y + h//2],
                            'aspect_ratio': aspect_ratio
                        })
                        print(f"Valid detection: conf={confidence:.2f}, AR={aspect_ratio:.1f}, size=({w}x{h})")
        
        return detections
    
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
                    'age': self.current_tracks[best_match]['age'] + 1
                }
                used_track_ids.add(best_match)
            else:
                # Create new track
                new_tracks[self.track_id_counter] = {
                    'bbox': detection['bbox'],
                    'center': center,
                    'confidence': detection['confidence'],
                    'age': 1
                }
                self.track_id_counter += 1
        
        return new_tracks
    
    def process_frame(self, frame):
        """Process a single frame for tracking"""
        if not self.is_tracking:
            return frame
        
        # Detect people
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
            aspect_ratio = track_info.get('aspect_ratio', 0)
            
            # Store tracking data
            try:
                self.db.add_person_detection(track_id, x, y, w, h, confidence, self.session_id)
            except Exception as e:
                print(f"Error storing data: {e}")
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label with confidence and aspect ratio
            label = f"Person {track_id} ({confidence:.2f}) AR:{aspect_ratio:.1f}"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Update session statistics
        try:
            self.db.update_session_stats(self.session_id, self.people_count, self.total_people_count)
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        # Add count overlay
        cv2.putText(frame, f"Current: {self.people_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Total: {self.total_people_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame
    
    def start_tracking(self):
        """Start tracking"""
        self.is_tracking = True
        print("Tracking started")
    
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
