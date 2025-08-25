from flask import Flask, render_template, Response, request, jsonify
import cv2
import json
from minimal_tracking import MinimalPeopleTracker, VideoStream
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global variables
tracker = None
video_stream = None

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
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
            tracker = MinimalPeopleTracker()
        
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
            stats = tracker.get_stats()
            stats['duration'] = '0s'  # Simplified for now
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

@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html'), 500

if __name__ == '__main__':
    print("Starting FaceScannerPro People Tracking Application...")
    print("Features: OpenCV HOG People Detection + Simple Tracking")
    print("Access the dashboard at: http://localhost:8080")
    print("Note: This minimal version uses HOG detector instead of YOLO")
    
    app.run(debug=False, host='127.0.0.1', port=8080, threaded=True)
