import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime import DeepSort
import json
import uuid
from datetime import datetime
from models import db, Person, TrackingSession, PersonIdentity
import threading
import time

class PeopleTracker:
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.5):
        """Initialize the people tracker with YOLO and DeepSORT"""
        self.model = YOLO(model_path)
        self.tracker = DeepSort(max_age=50, n_init=3)
        self.conf_threshold = conf_threshold
        self.session_id = str(uuid.uuid4())
        self.current_tracks = {}
        self.people_count = 0
        self.total_people_count = 0
        self.known_faces = self.load_known_faces()
        self.is_tracking = False
        
        # Create new tracking session
        self.create_tracking_session()
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        known_faces = {}
        try:
            identities = PersonIdentity.query.all()
            for identity in identities:
                encoding = np.array(json.loads(identity.face_encoding))
                known_faces[identity.name] = encoding
        except Exception as e:
            print(f"Error loading known faces: {e}")
        return known_faces
    
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
        """Detect people in frame using YOLO"""
        results = self.model(frame, conf=self.conf_threshold, classes=[0])  # Class 0 is 'person'
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    
                    # Convert to DeepSORT format [x, y, w, h]
                    detection = [x1, y1, x2 - x1, y2 - y1, conf]
                    detections.append(detection)
        
        return detections
    
    def identify_face(self, face_image):
        """Identify face using simple face detection (placeholder for face recognition)"""
        try:
            # Simple face detection using OpenCV (placeholder for face recognition)
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Return unknown for now - face recognition can be added later
                return "Unknown", None
            
        except Exception as e:
            print(f"Error in face identification: {e}")
        
        return None, None
    
    def process_frame(self, frame):
        """Process a single frame for tracking"""
        if not self.is_tracking:
            return frame
        
        # Detect people
        detections = self.detect_people(frame)
        
        # Update tracker
        tracks = self.tracker.update_tracks(detections, frame=frame)
        
        current_track_ids = set()
        
        for track in tracks:
            if not track.is_confirmed():
                continue
            
            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            
            current_track_ids.add(track_id)
            
            # Extract face for identification
            face_crop = frame[y1:y2, x1:x2]
            identity_name, face_encoding = self.identify_face(face_crop)
            
            # Store tracking data
            self.store_tracking_data(track_id, x1, y1, x2-x1, y2-y1, track.get_det_conf(), face_encoding)
            
            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"ID: {track_id}"
            if identity_name:
                label += f" - {identity_name}"
            
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Update counts
        self.people_count = len(current_track_ids)
        if current_track_ids - set(self.current_tracks.keys()):
            # New people detected
            new_people = len(current_track_ids - set(self.current_tracks.keys()))
            self.total_people_count += new_people
        
        self.current_tracks = {tid: True for tid in current_track_ids}
        
        # Update session in database
        self.update_session_stats()
        
        # Add count overlay
        cv2.putText(frame, f"Current: {self.people_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Total: {self.total_people_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame
    
    def store_tracking_data(self, track_id, x, y, width, height, confidence, face_encoding):
        """Store tracking data in database"""
        try:
            face_encoding_json = None
            if face_encoding is not None:
                face_encoding_json = json.dumps(face_encoding.tolist())
            
            person = Person(
                track_id=track_id,
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                confidence=float(confidence),
                face_encoding=face_encoding_json,
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
    
    def add_known_person(self, name, face_image):
        """Add a known person to the database (placeholder implementation)"""
        try:
            # Placeholder for face recognition implementation
            # For now, just store the name without face encoding
            identity = PersonIdentity(
                name=name,
                face_encoding=json.dumps([])  # Empty encoding for now
            )
            
            db.session.add(identity)
            db.session.commit()
            
            print(f"Added known person: {name}")
            return True
            
        except Exception as e:
            print(f"Error adding known person: {e}")
            db.session.rollback()
        
        return False

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
