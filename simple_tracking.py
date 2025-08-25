import cv2
import numpy as np
import json
import uuid
from datetime import datetime
from models import db, Person, TrackingSession, PersonIdentity
import threading
import time

class SimplePeopleTracker:
    def __init__(self, conf_threshold=0.5):
        """Initialize the people tracker with OpenCV HOG detector"""
        # Use OpenCV's HOG (Histogram of Oriented Gradients) people detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        self.conf_threshold = conf_threshold
        self.session_id = str(uuid.uuid4())
        self.current_tracks = {}
        self.people_count = 0
        self.total_people_count = 0
        self.is_tracking = False
        self.track_id_counter = 1
        
        # Simple tracking parameters
        self.track_threshold = 50  # Pixel distance threshold for tracking
        
        # Create new tracking session
        self.create_tracking_session()
    
    def create_tracking_session(self):
        """Create a new tracking session in database"""
        try:
            session = TrackingSession(session_id=self.session_id)
            db.session.add(session)
            db.session.commit()
            print(f"Created tracking session: {self.session_id}")
        except Exception as e:
            print(f"Error creating session: {e}")
    
    def detect_people(self, frame):
        """Detect people in frame using HOG detector"""
        # Detect people
        boxes, weights = self.hog.detectMultiScale(frame, 
                                                  winStride=(8, 8),
                                                  padding=(32, 32),
                                                  scale=1.05)
        
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > self.conf_threshold:
                detections.append({
                    'bbox': [x, y, w, h],
                    'confidence': float(weights[i]),
                    'center': [x + w//2, y + h//2]
                })
        
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
            
            # Store tracking data
            self.store_tracking_data(track_id, x, y, w, h, confidence)
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label
            label = f"ID: {track_id} ({confidence:.2f})"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Update session statistics
        self.update_session_stats()
        
        # Add count overlay
        cv2.putText(frame, f"Current: {self.people_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Total: {self.total_people_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame
    
    def store_tracking_data(self, track_id, x, y, width, height, confidence):
        """Store tracking data in database"""
        try:
            person = Person(
                track_id=track_id,
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                confidence=float(confidence),
                face_encoding=None,
                session_id=self.session_id
            )
            
            db.session.add(person)
            db.session.commit()
            
        except Exception as e:
            print(f"Error storing tracking data: {e}")
            db.session.rollback()
    
    def update_session_stats(self):
        """Update session statistics"""
        try:
            session = TrackingSession.query.filter_by(session_id=self.session_id).first()
            if session:
                session.current_people_count = self.people_count
                session.total_people_count = self.total_people_count
                db.session.commit()
        except Exception as e:
            print(f"Error updating session stats: {e}")
    
    def start_tracking(self):
        """Start tracking"""
        self.is_tracking = True
        print("Tracking started")
    
    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        try:
            session = TrackingSession.query.filter_by(session_id=self.session_id).first()
            if session:
                session.status = 'stopped'
                session.end_time = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            print(f"Error stopping session: {e}")
        print("Tracking stopped")

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
