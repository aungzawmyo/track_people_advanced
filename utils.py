import json
from datetime import datetime, timedelta

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def calculate_session_duration(start_time, end_time=None):
    """Calculate session duration"""
    if end_time is None:
        end_time = datetime.utcnow()
    
    duration = end_time - start_time
    return duration.total_seconds()

def format_duration(seconds):
    """Format duration in human readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def validate_bbox(x, y, width, height, frame_width, frame_height):
    """Validate bounding box coordinates"""
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        return False
    
    if x + width > frame_width or y + height > frame_height:
        return False
    
    return True

def calculate_bbox_center(x, y, width, height):
    """Calculate center point of bounding box"""
    center_x = x + width / 2
    center_y = y + height / 2
    return center_x, center_y

def get_session_stats(session_id):
    """Get comprehensive session statistics"""
    from models import TrackingSession, Person
    
    try:
        session = TrackingSession.query.filter_by(session_id=session_id).first()
        if not session:
            return None
        
        # Get all person detections for this session
        detections = Person.query.filter_by(session_id=session_id).all()
        
        # Calculate unique tracks
        unique_tracks = len(set([p.track_id for p in detections]))
        
        # Calculate session duration
        duration = calculate_session_duration(
            session.start_time, 
            session.end_time
        )
        
        stats = {
            'session_id': session.session_id,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'duration': format_duration(duration),
            'duration_seconds': duration,
            'total_detections': len(detections),
            'unique_people': unique_tracks,
            'current_people': session.current_people_count,
            'status': session.status
        }
        
        return stats
        
    except Exception as e:
        print(f"Error getting session stats: {e}")
        return None
