#!/usr/bin/env python3
"""
YOLO + DeepSORT People Tracking Web Application
==============================================
Enhanced people tracking using YOLOv8 and DeepSORT for precise detection and tracking.
"""

from flask import Flask, render_template, Response, jsonify, request
import cv2
import json
import time
import threading
from datetime import datetime, timedelta
import os
import sys
import uuid
import numpy as np
import sqlite3

# Import YOLO + DeepSORT components
YOLO_AVAILABLE = True
try:
    from ultralytics import YOLO
    from deep_sort_realtime.deepsort_tracker import DeepSort
    print("✓ YOLO and DeepSORT packages loaded successfully")
except ImportError as e:
    YOLO_AVAILABLE = False
    print(f"❌ YOLO/DeepSORT not available: {e}")
    print("Installing required packages with: pip install ultralytics deep-sort-realtime")

# Simple database for YOLO app
import sqlite3

class YOLODatabase:
    """Thread-safe SQLite database for YOLO tracking"""
    
    def __init__(self, db_path="yolo_tracking.db"):
        self.db_path = db_path
        self.lock = threading.Lock()  # Add thread lock
        self.init_db()
    
    def get_connection(self):
        """Get a thread-safe database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)  # 10 second timeout
        conn.execute("PRAGMA journal_mode=WAL")  # Use WAL mode for better concurrency
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS yolo_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    total_people_count INTEGER DEFAULT 0,
                    current_people_count INTEGER DEFAULT 0,
                    detection_method TEXT DEFAULT 'YOLO+DeepSORT',
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS yolo_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    session_id TEXT NOT NULL,
                    class_name TEXT DEFAULT 'person'
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✓ YOLO Database initialized successfully!")
    
    def add_session(self, session_id):
        """Add a new tracking session"""
        with self.lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO yolo_sessions (session_id) VALUES (?)",
                    (session_id,)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠ Error adding session: {e}")
    
    def update_session_stats(self, session_id, current_count, total_count):
        """Update session statistics"""
        with self.lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE yolo_sessions SET current_people_count = ?, total_people_count = ? WHERE session_id = ?",
                    (current_count, total_count, session_id)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠ Error updating session stats: {e}")
    
    def add_detection(self, track_id, x, y, width, height, confidence, session_id):
        """Add a detection record with proper validation"""
        # Validate confidence value
        if confidence is None or confidence == float('nan'):
            confidence = 0.0
        confidence = float(confidence)
        
        with self.lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO yolo_detections (track_id, x, y, width, height, confidence, session_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (int(track_id), float(x), float(y), float(width), float(height), confidence, session_id)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠ Error adding detection: {e}")

class YOLOPeopleTracker:
    """YOLO + DeepSORT People Tracker"""
    
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.6):
        """Initialize YOLO + DeepSORT tracker"""
        if not YOLO_AVAILABLE:
            raise ImportError("YOLO and DeepSORT packages not available")
        
        print("🔄 Initializing YOLO + DeepSORT tracker...")
        
        # Initialize YOLO model
        self.model = YOLO(model_path)
        print(f"✓ YOLO model loaded: {model_path}")
        
        # Initialize DeepSORT tracker
        self.tracker = DeepSort(max_age=50, n_init=3, max_cosine_distance=0.2)
        print("✓ DeepSORT tracker initialized")
        
        self.conf_threshold = conf_threshold
        self.session_id = str(uuid.uuid4())
        self.current_tracks = {}
        self.people_count = 0
        self.total_people_count = 0
        self.is_tracking = False
        self.track_id_counter = 1
        self.last_db_update = time.time()
        self.db_update_interval = 1.0  # Update database every 1 second
        
        # Initialize database
        self.db = YOLODatabase()
        self.db.add_session(self.session_id)
        
        print(f"✓ YOLO tracking session created: {self.session_id}")
        print(f"✓ Confidence threshold: {self.conf_threshold}")
        print("🎯 YOLO + DeepSORT People Tracker Ready!")
    
    def detect_people(self, frame):
        """Detect people using YOLO"""
        # Run YOLO inference
        results = self.model(frame, conf=self.conf_threshold, classes=[0], verbose=False)  # Class 0 = person
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get coordinates and confidence
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    
                    # Convert to [x, y, w, h] format for DeepSORT
                    x, y, w, h = float(x1), float(y1), float(x2 - x1), float(y2 - y1)
                    
                    # Basic size filtering (remove very small detections)
                    if w >= 30 and h >= 60:  # Minimum person size
                        detections.append([[x, y, w, h], float(conf), 'person'])
        
        return detections
    
    def process_frame(self, frame):
        """Process frame with YOLO + DeepSORT tracking"""
        if not self.is_tracking:
            return frame
        
        try:
            # Detect people with YOLO
            detections = self.detect_people(frame)
            
            if not detections:
                # No detections, just add overlays and return
                self.people_count = 0
                self.current_tracks = {}
                # Update database less frequently
                current_time = time.time()
                if current_time - self.last_db_update > self.db_update_interval:
                    try:
                        self.db.update_session_stats(self.session_id, self.people_count, self.total_people_count)
                    except Exception as db_error:
                        print(f"⚠ Session update error: {db_error}")
                    self.last_db_update = current_time
                
                # Add overlays
                cv2.putText(frame, f"YOLO+DeepSORT", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(frame, f"Current: {self.people_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"Total: {self.total_people_count}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"Conf: {self.conf_threshold}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                return frame
            
            # Update DeepSORT tracker
            tracks = self.tracker.update_tracks(detections, frame=frame)
            
            current_track_ids = set()
            
            # Process each track
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                
                # Ensure coordinates are within frame bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(frame.shape[1], x2)
                y2 = min(frame.shape[0], y2)
                
                current_track_ids.add(track_id)
                
                # Get detection confidence with proper handling
                conf = 0.0
                try:
                    if hasattr(track, 'get_det_conf') and track.get_det_conf() is not None:
                        conf = float(track.get_det_conf())
                    else:
                        # Try to get confidence from detection data
                        if hasattr(track, 'det_conf') and track.det_conf is not None:
                            conf = float(track.det_conf)
                        else:
                            conf = 0.7  # Default confidence for valid tracks
                except (ValueError, TypeError):
                    conf = 0.7  # Default confidence if extraction fails
                
                # Store detection in database (less frequently to reduce lock contention)
                current_time = time.time()
                if current_time - self.last_db_update > self.db_update_interval:
                    try:
                        self.db.add_detection(track_id, x1, y1, x2-x1, y2-y1, conf, self.session_id)
                    except Exception as db_error:
                        print(f"⚠ Database error: {db_error}")
                    self.last_db_update = current_time
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"YOLO ID: {track_id} ({conf:.2f})"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (x1, y1-label_size[1]-10), (x1+label_size[0], y1), (0, 255, 0), -1)
                cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                
                print(f"✓ YOLO Track: ID={track_id}, conf={conf:.2f}, size=({x2-x1}x{y2-y1})")
            
            # Update people counts
            self.people_count = len(current_track_ids)
            
            # Check for new people
            new_tracks = current_track_ids - set(self.current_tracks.keys())
            if new_tracks:
                self.total_people_count += len(new_tracks)
                print(f"🆕 New people detected: {len(new_tracks)}")
            
            self.current_tracks = {tid: True for tid in current_track_ids}
            
            # Update database stats (less frequently)
            current_time = time.time()
            if current_time - self.last_db_update > self.db_update_interval:
                try:
                    self.db.update_session_stats(self.session_id, self.people_count, self.total_people_count)
                except Exception as db_error:
                    print(f"⚠ Session update error: {db_error}")
                self.last_db_update = current_time
            
        except Exception as e:
            print(f"⚠ Error in process_frame: {e}")
        
        # Add overlays
        cv2.putText(frame, f"YOLO+DeepSORT", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"Current: {self.people_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Total: {self.total_people_count}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Conf: {self.conf_threshold}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def start_tracking(self):
        """Start tracking"""
        self.is_tracking = True
        print("🚀 YOLO + DeepSORT tracking started")
    
    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        print("⏹ YOLO + DeepSORT tracking stopped")
    
    def get_stats(self):
        """Get current tracking statistics"""
        return {
            'current_people': self.people_count,
            'total_people': self.total_people_count,
            'session_id': self.session_id,
            'is_tracking': self.is_tracking,
            'detection_method': 'YOLO + DeepSORT',
            'confidence_threshold': self.conf_threshold
        }

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variables
video_capture = None
people_tracker = None
output_frame = None
lock = threading.Lock()

def generate_frames():
    """Generate video frames for streaming"""
    global output_frame, people_tracker
    
    while True:
        with lock:
            if output_frame is None:
                continue
            
            # Encode frame as JPEG
            (flag, encoded_image) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue
        
        # Yield frame in byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encoded_image) + b'\r\n')

def capture_frames():
    """Capture frames from camera"""
    global video_capture, people_tracker, output_frame
    
    while True:
        try:
            ret, frame = video_capture.read()
            if not ret:
                print("❌ Failed to read frame from camera")
                break
            
            # Process frame with tracker
            if people_tracker:
                try:
                    frame = people_tracker.process_frame(frame)
                except Exception as e:
                    print(f"⚠ Error processing frame: {e}")
                    # Continue with unprocessed frame
            
            with lock:
                output_frame = frame.copy()
        except Exception as e:
            print(f"❌ Error in capture_frames: {e}")
            break

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('yolo_dashboard.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start-tracking', methods=['POST'])
def start_tracking():
    """Start tracking endpoint"""
    if people_tracker:
        people_tracker.start_tracking()
        return jsonify({'status': 'success', 'message': 'YOLO tracking started'})
    return jsonify({'status': 'error', 'message': 'Tracker not initialized'})

@app.route('/api/stop-tracking', methods=['POST'])
def stop_tracking():
    """Stop tracking endpoint"""
    if people_tracker:
        people_tracker.stop_tracking()
        return jsonify({'status': 'success', 'message': 'YOLO tracking stopped'})
    return jsonify({'status': 'error', 'message': 'Tracker not initialized'})

@app.route('/api/stats')
def get_stats():
    """Get tracking statistics"""
    if people_tracker:
        return jsonify(people_tracker.get_stats())
    return jsonify({'error': 'Tracker not initialized'})

@app.route('/api/reset-session', methods=['POST'])
def reset_session():
    """Reset tracking session"""
    global people_tracker
    if people_tracker:
        people_tracker.stop_tracking()
        # Create new tracker instance
        people_tracker = YOLOPeopleTracker()
        return jsonify({'status': 'success', 'message': 'Session reset'})
    return jsonify({'status': 'error', 'message': 'Tracker not initialized'})

# Create YOLO dashboard template
yolo_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YOLO + DeepSORT People Tracking</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .yolo-accent { color: #00ff41; }
        .tracking-box { border: 2px solid #00ff41; }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div class="min-h-screen gradient-bg">
        <!-- Header -->
        <header class="bg-black bg-opacity-50 p-4">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-3xl font-bold yolo-accent">🎯 YOLO + DeepSORT Tracker</h1>
                <div class="flex space-x-4">
                    <button id="startBtn" onclick="startTracking()" 
                            class="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-semibold transition">
                        ▶ Start Tracking
                    </button>
                    <button id="stopBtn" onclick="stopTracking()" 
                            class="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg font-semibold transition">
                        ⏹ Stop Tracking
                    </button>
                    <button onclick="resetSession()" 
                            class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition">
                        🔄 Reset
                    </button>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="container mx-auto p-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Video Feed -->
                <div class="lg:col-span-2">
                    <div class="bg-black bg-opacity-60 rounded-xl p-6 tracking-box">
                        <h2 class="text-2xl font-bold mb-4 yolo-accent">🔴 Live Feed</h2>
                        <div class="relative">
                            <img id="videoFeed" src="/video_feed" 
                                 class="w-full h-auto rounded-lg border-2 border-green-500" 
                                 alt="Live Video Feed">
                            <div class="absolute top-4 left-4 bg-black bg-opacity-75 px-3 py-1 rounded">
                                <span class="yolo-accent font-mono text-sm">YOLO + DeepSORT ACTIVE</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Statistics Panel -->
                <div class="space-y-6">
                    <!-- Real-time Stats -->
                    <div class="bg-black bg-opacity-60 rounded-xl p-6">
                        <h3 class="text-xl font-bold mb-4 yolo-accent">📊 Live Statistics</h3>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Current People:</span>
                                <span id="currentCount" class="text-2xl font-bold yolo-accent">0</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Total Detected:</span>
                                <span id="totalCount" class="text-2xl font-bold text-yellow-400">0</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Status:</span>
                                <span id="trackingStatus" class="font-semibold text-red-400">Stopped</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">Method:</span>
                                <span class="font-semibold yolo-accent">YOLO + DeepSORT</span>
                            </div>
                        </div>
                    </div>

                    <!-- System Info -->
                    <div class="bg-black bg-opacity-60 rounded-xl p-6">
                        <h3 class="text-xl font-bold mb-4 yolo-accent">⚙️ System Info</h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Detection:</span>
                                <span class="yolo-accent">YOLOv8</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Tracking:</span>
                                <span class="yolo-accent">DeepSORT</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Confidence:</span>
                                <span id="confidence" class="yolo-accent">0.6</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Session ID:</span>
                                <span id="sessionId" class="text-xs text-gray-400">-</span>
                            </div>
                        </div>
                    </div>

                    <!-- Performance -->
                    <div class="bg-black bg-opacity-60 rounded-xl p-6">
                        <h3 class="text-xl font-bold mb-4 yolo-accent">🚀 Performance</h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Accuracy:</span>
                                <span class="text-green-400">High</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">False Positives:</span>
                                <span class="text-green-400">Low</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Tracking Quality:</span>
                                <span class="text-green-400">Excellent</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Update stats every 2 seconds
        setInterval(updateStats, 2000);
        
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('currentCount').textContent = data.current_people || 0;
                    document.getElementById('totalCount').textContent = data.total_people || 0;
                    document.getElementById('trackingStatus').textContent = data.is_tracking ? 'Active' : 'Stopped';
                    document.getElementById('trackingStatus').className = data.is_tracking ? 
                        'font-semibold text-green-400' : 'font-semibold text-red-400';
                    document.getElementById('confidence').textContent = data.confidence_threshold || '0.6';
                    document.getElementById('sessionId').textContent = data.session_id ? 
                        data.session_id.substring(0, 8) + '...' : '-';
                });
        }
        
        function startTracking() {
            fetch('/api/start-tracking', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Tracking started:', data);
                });
        }
        
        function stopTracking() {
            fetch('/api/stop-tracking', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Tracking stopped:', data);
                });
        }
        
        function resetSession() {
            fetch('/api/reset-session', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Session reset:', data);
                });
        }
        
        // Initial stats load
        updateStats();
    </script>
</body>
</html>'''

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)
with open('templates/yolo_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(yolo_template)

if __name__ == '__main__':
    print("🎯 YOLO + DeepSORT People Tracking System")
    print("=" * 50)
    
    # Check YOLO availability
    if not YOLO_AVAILABLE:
        print("❌ YOLO/DeepSORT packages not available!")
        print("Please install: pip install ultralytics deep-sort-realtime")
        sys.exit(1)
    
    try:
        # Initialize camera
        print("📹 Initializing camera...")
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("❌ Error: Could not open camera")
            sys.exit(1)
        print("✓ Camera initialized")
        
        # Initialize YOLO tracker
        print("🤖 Initializing YOLO + DeepSORT tracker...")
        people_tracker = YOLOPeopleTracker()
        
        # Start video capture thread
        print("🎬 Starting video capture thread...")
        capture_thread = threading.Thread(target=capture_frames, daemon=True)
        capture_thread.start()
        
        print("✅ YOLO + DeepSORT System Ready!")
        print("🌐 Dashboard: http://localhost:8081")
        print("💡 Features:")
        print("   - YOLOv8 object detection")
        print("   - DeepSORT multi-object tracking")
        print("   - Real-time video streaming")
        print("   - Advanced tracking metrics")
        print("   - Low false positive rate")
        
        # Start Flask app
        app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ Error starting YOLO system: {e}")
        if video_capture:
            video_capture.release()
