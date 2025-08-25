from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
from precise_tracking import PrecisePeopleTracker, VideoStream

app = Flask(__name__)

# Global variables
video_stream = None
tracker = None
stream_lock = threading.Lock()

def initialize_system():
    """Initialize the video stream and tracker"""
    global video_stream, tracker
    
    try:
        # Initialize precise people tracker
        tracker = PrecisePeopleTracker(conf_threshold=0.5)
        
        # Initialize video stream
        video_stream = VideoStream(source=0)
        video_stream.set_tracker(tracker)
        video_stream.start()
        
        print("✓ Precision People Tracking System Ready")
        return True
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        return False

def generate_frames():
    """Generate frames for video streaming"""
    global video_stream
    
    while True:
        if video_stream is None:
            time.sleep(0.1)
            continue
            
        try:
            with stream_lock:
                ret, frame = video_stream.get_frame()
            
            if ret:
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)
        except Exception as e:
            print(f"Error generating frame: {e}")
            time.sleep(0.1)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start-tracking', methods=['POST'])
def start_tracking():
    """Start people tracking"""
    try:
        if tracker:
            tracker.start_tracking()
            return jsonify({'status': 'success', 'message': 'Precision tracking started'})
        else:
            return jsonify({'status': 'error', 'message': 'Tracker not initialized'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stop-tracking', methods=['POST'])
def stop_tracking():
    """Stop people tracking"""
    try:
        if tracker:
            tracker.stop_tracking()
            return jsonify({'status': 'success', 'message': 'Tracking stopped'})
        else:
            return jsonify({'status': 'error', 'message': 'Tracker not initialized'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stats')
def get_stats():
    """Get current tracking statistics"""
    try:
        if tracker:
            stats = tracker.get_stats()
            return jsonify(stats)
        else:
            return jsonify({
                'current_people': 0,
                'total_people': 0,
                'is_tracking': False,
                'status': 'not_initialized'
            })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/reset-session', methods=['POST'])
def reset_session():
    """Reset current tracking session"""
    try:
        if tracker:
            tracker.stop_tracking()
            # Reset counters
            tracker.people_count = 0
            tracker.total_people_count = 0
            tracker.current_tracks = {}
            tracker.track_id_counter = 1
            return jsonify({'status': 'success', 'message': 'Session reset'})
        else:
            return jsonify({'status': 'error', 'message': 'Tracker not initialized'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🎯 FaceScannerPro - Precision People Tracking")
    print("=" * 50)
    print("Features:")
    print("✓ Multi-method people detection (HOG + Face + Motion)")
    print("✓ Strict validation to prevent false positives")
    print("✓ Real-time video streaming")
    print("✓ SQLite database storage")
    print("✓ Web dashboard with Tailwind CSS")
    print("=" * 50)
    
    # Initialize the system
    if initialize_system():
        print("🚀 Starting web server...")
        print("🌐 Dashboard: http://localhost:8080")
        print("💡 Tips:")
        print("   - Click 'Start Tracking' to begin detection")
        print("   - System uses strict validation to avoid false positives")
        print("   - Green boxes = validated people detections")
        print("")
        
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    else:
        print("❌ Failed to initialize system. Please check camera and dependencies.")
