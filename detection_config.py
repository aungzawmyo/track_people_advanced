# FaceScannerPro - People Detection Configuration

## Detection Parameters
# Adjust these values to improve people-only detection

# Confidence threshold (0.0 to 1.0)
# Higher = fewer false positives, might miss some people
# Lower = more detections, might include objects
CONFIDENCE_THRESHOLD = 0.8

# Size constraints (pixels)
MIN_PERSON_WIDTH = 30      # Minimum width for a person
MIN_PERSON_HEIGHT = 60     # Minimum height for a person  
MAX_PERSON_WIDTH = 300     # Maximum width for a person
MAX_PERSON_HEIGHT = 500    # Maximum height for a person

# Aspect ratio constraints (height/width)
# People are typically taller than they are wide
MIN_ASPECT_RATIO = 1.5     # Minimum height/width ratio
MAX_ASPECT_RATIO = 4.0     # Maximum height/width ratio

# HOG Detection parameters
WIN_STRIDE = (8, 8)        # Detection window stride
PADDING = (32, 32)         # Padding around detection window
SCALE = 1.05               # Scale factor between detection scales
GROUP_THRESHOLD = 2        # Minimum detections to group together

# Tracking parameters
TRACK_THRESHOLD = 50       # Maximum pixel distance for track association

"""
## Tuning Guide

### To reduce false positives (objects detected as people):
- Increase CONFIDENCE_THRESHOLD (try 0.9 or 1.0)
- Increase MIN_PERSON_WIDTH and MIN_PERSON_HEIGHT
- Reduce MAX_PERSON_WIDTH and MAX_PERSON_HEIGHT
- Increase GROUP_THRESHOLD to 3 or 4

### To detect more people (if missing some):
- Decrease CONFIDENCE_THRESHOLD (try 0.6 or 0.7)
- Decrease MIN_PERSON_WIDTH and MIN_PERSON_HEIGHT
- Increase MAX_PERSON_WIDTH and MAX_PERSON_HEIGHT
- Decrease GROUP_THRESHOLD to 1

### For better tracking:
- Adjust TRACK_THRESHOLD based on camera distance
- Closer camera: lower value (30-40)
- Farther camera: higher value (60-80)

## Common Issues and Solutions

### Problem: Detecting chairs, poles, or furniture as people
Solution: Increase CONFIDENCE_THRESHOLD to 0.9+

### Problem: Missing people in the background
Solution: Decrease MIN_PERSON_WIDTH and MIN_PERSON_HEIGHT

### Problem: Detecting parts of people as separate people
Solution: Increase GROUP_THRESHOLD and adjust size constraints

### Problem: Losing track of people frequently
Solution: Increase TRACK_THRESHOLD value
"""
