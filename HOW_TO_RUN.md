# 🚀 How to Run FaceScannerPro - Step by Step Guide

## 📋 Quick Start (For Immediate Use)

### Option 1: Automated Startup (Easiest) ⭐
```powershell
# Simply double-click the start.bat file
# OR run in PowerShell:
.\start.bat
```

### Option 2: Manual Commands
```powershell
# 1. Navigate to project directory
cd "D:\Workspace\python\FaceScannerPro\tracker"

# 2. Activate virtual environment (already exists)
.\.venv\Scripts\activate.bat

# 3. Run the application
python minimal_app.py

# 4. Open browser: http://localhost:8080
```

## 🔧 Detailed Setup (First Time Users)

### 1. Navigate to Project Directory
```powershell
cd "D:\Workspace\python\FaceScannerPro\tracker"
```

### 2. Create Virtual Environment (Recommended)
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\activate.bat

# Your prompt should now show (.venv) at the beginning
```

### 3. Install Dependencies
```powershell
# Make sure you're in the virtual environment (.venv should be visible)
pip install -r requirements.txt

# Or install minimal packages individually:
pip install Flask opencv-python numpy
```

### 4. Test Installation
```powershell
python test_minimal.py
```

You should see:
```
✓ All tests passed! Your minimal environment is ready.
```

## 🏃‍♂️ Running the Application

### Method 1: Using Virtual Environment (Recommended)

#### Step 1: Open PowerShell/Command Prompt
```powershell
# Navigate to project directory
cd "D:\Workspace\python\FaceScannerPro\tracker"
```

#### Step 2: Activate Virtual Environment
```powershell
# Activate virtual environment
.\.venv\Scripts\activate.bat

# You should see (.venv) at the beginning of your prompt:
# (.venv) PS D:\Workspace\python\FaceScannerPro\tracker>
```

#### Step 3: Run the Application
```powershell
# Run the minimal application (recommended)
python minimal_app.py

# Or run the full application (if YOLO dependencies are installed)
python app.py
```

#### Step 4: Access the Dashboard
- Open your web browser
- Navigate to: **http://localhost:8080**
- Start tracking by clicking the "Start" button

#### Step 5: Stop the Application
```powershell
# In the terminal where the app is running, press:
Ctrl + C

# To deactivate virtual environment:
deactivate
```

### Method 2: Using System Python (Alternative)

#### Step 1: Open PowerShell/Command Prompt
```powershell
cd "D:\Workspace\python\FaceScannerPro\tracker"
```

#### Step 2: Run Directly
```powershell
# Ensure packages are installed globally
pip install Flask opencv-python numpy

# Run the application
python minimal_app.py
```

## 📱 Complete Startup Sequence

### Windows PowerShell Commands:
```powershell
# 1. Navigate to project
cd "D:\Workspace\python\FaceScannerPro\tracker"

# 2. Activate virtual environment
.\.venv\Scripts\activate.bat

# 3. Verify installation (optional)
python test_minimal.py

# 4. Start the application
python minimal_app.py

# 5. Open browser to http://localhost:8080
```

### Expected Output:
```
Starting FaceScannerPro People Tracking Application...
Features: OpenCV HOG People Detection + Simple Tracking
Access the dashboard at: http://localhost:8080
Note: This minimal version uses HOG detector instead of YOLO
 * Serving Flask app 'minimal_app'
 * Debug mode: off
 * Running on http://127.0.0.1:8080
Press CTRL+C to quit
```

## 🔄 Daily Usage Workflow

### Quick Start (After Initial Setup):
```powershell
# 1. Open PowerShell
# 2. Navigate and activate
cd "D:\Workspace\python\FaceScannerPro\tracker" && .\.venv\Scripts\activate.bat

# 3. Run application
python minimal_app.py

# 4. Open browser: http://localhost:8080
```

### One-Line Startup:
```powershell
cd "D:\Workspace\python\FaceScannerPro\tracker" && .\.venv\Scripts\activate.bat && python minimal_app.py
```

## 🛠️ Troubleshooting

### Virtual Environment Issues:
```powershell
# If .venv doesn't exist, create it:
python -m venv .venv

# If activation fails, try:
.\.venv\Scripts\Activate.ps1

# Or use full path:
D:\Workspace\python\FaceScannerPro\tracker\.venv\Scripts\activate.bat
```

### Package Installation Issues:
```powershell
# Upgrade pip first:
python -m pip install --upgrade pip

# Install packages with specific versions:
pip install Flask==2.3.3 opencv-python==4.10.0.84 numpy

# If still issues, install one by one:
pip install Flask
pip install opencv-python
pip install numpy
```

### Port Issues:
```powershell
# If port 8080 is busy, the app will show an error
# Check what's using the port:
netstat -ano | findstr :8080

# Or modify the port in minimal_app.py:
# Change port=8080 to port=8081 or any available port
```

### Camera Issues:
```powershell
# Test camera access:
python test_minimal.py

# If camera fails, check:
# 1. Camera is connected and not used by other apps
# 2. Camera permissions in Windows settings
# 3. Try different camera index in VideoStream(source=1)
```

## 📁 Project Structure Reference
```
FaceScannerPro/tracker/
├── .venv/                  # Virtual environment (after creation)
├── minimal_app.py          # Main application file 🏃‍♂️
├── minimal_tracking.py     # Tracking logic
├── test_minimal.py         # Test script
├── templates/              # HTML templates
├── static/                # CSS/JS files
├── requirements.txt       # Dependencies
└── people_tracking.db     # Database (created automatically)
```

## 🎯 Quick Reference Commands

### Environment Management:
```powershell
# Create environment
python -m venv .venv

# Activate environment (Windows)
.\.venv\Scripts\activate.bat

# Deactivate environment
deactivate

# Check if in environment
# Look for (.venv) in prompt
```

### Application Commands:
```powershell
# Test setup
python test_minimal.py

# Run minimal version (recommended)
python minimal_app.py

# Run full version (needs YOLO)
python app.py

# Stop application
Ctrl + C
```

### Web Access:
- **Dashboard**: http://localhost:8080
- **Video Feed**: http://localhost:8080/video_feed
- **API Stats**: http://localhost:8080/api/stats

## 💡 Pro Tips

1. **Always use virtual environment** to avoid package conflicts
2. **Test camera first** with `python test_minimal.py`
3. **Check terminal output** for any error messages
4. **Use Ctrl+C** to cleanly stop the application
5. **Keep terminal open** while using the web interface

## 🚀 Automated Startup Script

Create a `start.bat` file in the tracker directory:

```batch
@echo off
cd /d "D:\Workspace\python\FaceScannerPro\tracker"
call .venv\Scripts\activate.bat
echo Starting FaceScannerPro...
python minimal_app.py
pause
```

Then just double-click `start.bat` to run the application!

## ✅ Success Checklist

- [ ] Virtual environment activated (see `.venv` in prompt)
- [ ] No errors during package installation
- [ ] Test script passes all checks
- [ ] Application starts without errors
- [ ] Browser opens to http://localhost:8080
- [ ] Video feed displays in dashboard
- [ ] Start/Stop buttons work
- [ ] Statistics update in real-time

Your FaceScannerPro is ready to track people! 🎉
