# FaceScannerPro - People Tracking Application

A real-time people tracking application using YOLO + DeepSORT for detection and tracking, with a Flask web dashboard for monitoring.

## Features

- **Real-time People Detection**: Uses YOLOv8 for accurate person detection
- **Multi-object Tracking**: DeepSORT algorithm for consistent person tracking across frames
- **Face Recognition**: Optional face recognition for known person identification
- **Web Dashboard**: Modern web interface built with Flask and Tailwind CSS
- **Data Storage**: SQLite database for storing tracking data and statistics
- **Live Video Streaming**: Real-time video feed with bounding boxes and tracking IDs
- **Statistics & Analytics**: Comprehensive tracking statistics and session management

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Computer Vision**: OpenCV, YOLOv8 (Ultralytics), DeepSORT
- **Face Recognition**: face_recognition library
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: SQLite
- **Video Processing**: OpenCV for camera input and video streaming

## Project Structure

```
FaceScannerPro/tracker/
├── app.py              # Flask application entry point
├── tracking.py         # Core tracking logic (YOLO + DeepSORT)
├── models.py           # Database models (SQLAlchemy)
├── db.py              # Database initialization
├── utils.py           # Utility functions
├── requirements.txt   # Python dependencies
├── static/            # Static files (CSS, JS)
│   ├── style.css      # Custom styles with Tailwind
│   └── dashboard.js   # Dashboard JavaScript
└── templates/         # Jinja2 templates
    ├── base.html      # Base template
    └── dashboard.html # Main dashboard
```

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd d:\Workspace\python\FaceScannerPro\tracker
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download YOLOv8 model** (automatically downloaded on first run):
   ```python
   # The YOLOv8n model will be downloaded automatically when the app starts
   ```

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Access the dashboard**:
   Open your web browser and navigate to `http://localhost:5000`

3. **Start tracking**:
   - Click the "Start" button in the dashboard
   - Allow camera access when prompted
   - View real-time tracking with bounding boxes and person IDs

4. **Monitor statistics**:
   - View current people count
   - Track total people detected
   - Monitor session duration and status

## API Endpoints

- `GET /` - Main dashboard
- `GET /video_feed` - Video streaming endpoint
- `POST /api/start-tracking` - Start tracking
- `POST /api/stop-tracking` - Stop tracking
- `GET /api/stats` - Get current statistics
- `GET /api/sessions` - Get all tracking sessions
- `GET /api/session/<id>/detections` - Get detections for specific session
- `POST /api/add-known-person` - Add known person for identification
- `GET /api/known-persons` - Get all known persons

## Database Schema

### Tables:
- **persons**: Individual person detections with coordinates and timestamps
- **tracking_sessions**: Tracking session metadata and statistics  
- **person_identities**: Known person face encodings for identification

## Configuration

### Camera Settings
- Default camera source: `0` (first camera)
- To use a different camera or video file, modify the `VideoStream(source=0)` parameter in `app.py`

### YOLO Model
- Default model: `yolov8n.pt` (nano version for speed)
- For better accuracy, change to `yolov8s.pt`, `yolov8m.pt`, or `yolov8l.pt` in `tracking.py`

### Detection Threshold
- Default confidence threshold: `0.5`
- Adjust in `PeopleTracker` constructor for different sensitivity

## Development

### Adding New Features
1. **Database Models**: Add new models in `models.py`
2. **API Endpoints**: Add new routes in `app.py`
3. **Frontend Components**: Add templates in `templates/` and styles in `static/`
4. **Tracking Logic**: Extend functionality in `tracking.py`

### Debugging
- Enable Flask debug mode in `app.py`
- Check console output for tracking and database errors
- Use browser developer tools for frontend debugging

## Troubleshooting

### Common Issues:
1. **Camera not detected**: Check camera permissions and availability
2. **Model download fails**: Ensure internet connection for initial YOLOv8 download
3. **Performance issues**: Reduce video resolution or use lighter YOLO model
4. **Database errors**: Check file permissions for SQLite database creation

### Performance Optimization:
- Use GPU acceleration if available (CUDA)
- Adjust frame rate in `generate_frames()` function
- Optimize detection confidence threshold
- Use appropriate YOLO model size for your hardware

## License

This project is for educational and research purposes. Please ensure compliance with relevant licenses for included libraries.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions, please check the troubleshooting section or create an issue in the repository.
