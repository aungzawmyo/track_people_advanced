from flask import Flask, render_template, Response, request, jsonify
import cv2
import json
from models import db, Person, TrackingSession, PersonIdentity
from db import init_db
from simple_tracking import SimplePeopleTracker, VideoStream
from utils import get_session_stats, serialize_datetime
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///people_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Global variables
tracker = None
video_stream = None
tracking_thread = None

def generate_frames():
    """Generate video frames for streaming"""
    global video_stream
    
    if video_stream is None:
        video_stream = VideoStream(source=0)  # Use default camera
        if tracker:
            video_stream.set_tracker(tracker)
    
    video_stream.start()
    
    while True:
        try:
            ret, frame = video_stream.get_frame()
            if ret:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    break
            else:
                break
        except Exception as e:
            print(f"Error in frame generation: {e}")
            break
        
        time.sleep(0.1)  # Limit frame rate

@app.route('/')
def dashboard():
    """Main dashboard page"""
    session_info = {}
    
    if tracker:
        session_info = {
            'session_id': tracker.session_id,
            'start_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'is_tracking': tracker.is_tracking
        }
    
    return render_template('dashboard.html', **session_info)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start-tracking', methods=['POST'])
def start_tracking():
    """Start tracking API endpoint"""
    global tracker, video_stream
    
    try:
        if tracker is None:
            tracker = SimplePeopleTracker()
        
        tracker.start_tracking()
        
        if video_stream:
            video_stream.set_tracker(tracker)
        
        return jsonify({'status': 'success', 'message': 'Tracking started'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop-tracking', methods=['POST'])
def stop_tracking():
    """Stop tracking API endpoint"""
    global tracker
    
    try:
        if tracker:
            tracker.stop_tracking()
        
        return jsonify({'status': 'success', 'message': 'Tracking stopped'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get current tracking statistics"""
    try:
        if tracker:
            stats = {
                'current_people': tracker.people_count,
                'total_people': tracker.total_people_count,
                'is_tracking': tracker.is_tracking,
                'session_id': tracker.session_id,
                'status': 'active' if tracker.is_tracking else 'inactive'
            }
            
            # Get session stats from database
            session_stats = get_session_stats(tracker.session_id)
            if session_stats:
                stats.update(session_stats)
            
            return jsonify(stats)
        else:
            return jsonify({
                'current_people': 0,
                'total_people': 0,
                'is_tracking': False,
                'session_id': None,
                'status': 'inactive',
                'duration': '0s'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions')
def get_sessions():
    """Get all tracking sessions"""
    try:
        sessions = TrackingSession.query.order_by(TrackingSession.start_time.desc()).all()
        
        sessions_data = []
        for session in sessions:
            session_data = {
                'id': session.id,
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'total_people_count': session.total_people_count,
                'current_people_count': session.current_people_count,
                'status': session.status
            }
            sessions_data.append(session_data)
        
        return jsonify(sessions_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/detections')
def get_session_detections(session_id):
    """Get all detections for a specific session"""
    try:
        detections = Person.query.filter_by(session_id=session_id).all()
        
        detections_data = []
        for detection in detections:
            detection_data = {
                'id': detection.id,
                'track_id': detection.track_id,
                'timestamp': detection.timestamp.isoformat() if detection.timestamp else None,
                'x': detection.x,
                'y': detection.y,
                'width': detection.width,
                'height': detection.height,
                'confidence': detection.confidence
            }
            detections_data.append(detection_data)
        
        return jsonify(detections_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-known-person', methods=['POST'])
def add_known_person():
    """Add a known person for identification"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # For now, return success (face image upload would be implemented later)
        return jsonify({'status': 'success', 'message': f'Known person {name} added'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/known-persons')
def get_known_persons():
    """Get all known persons"""
    try:
        persons = PersonIdentity.query.all()
        
        persons_data = []
        for person in persons:
            person_data = {
                'id': person.id,
                'name': person.name,
                'created_at': person.created_at.isoformat() if person.created_at else None
            }
            persons_data.append(person_data)
        
        return jsonify(persons_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html'), 500

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created successfully!")
    
    print("Starting FaceScannerPro People Tracking Application...")
    print("Access the dashboard at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
