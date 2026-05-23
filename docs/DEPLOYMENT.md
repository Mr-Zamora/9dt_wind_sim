# PythonAnywhere Deployment Guide

This guide explains how to deploy AeroClass to PythonAnywhere (free tier).

## Prerequisites

- PythonAnywhere account (free or paid tier)
- GitHub account with the AeroClass repository

## Step 1: Clone Repository on PythonAnywhere

1. Log in to PythonAnywhere
2. Go to the "Consoles" tab and start a "Bash" console
3. Clone your repository:
```bash
git clone https://github.com/Mr-Zamora/9dt_wind_sim.git
cd 9dt_wind_sim
```

## Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Create Web App

1. Go to the "Web" tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration" (not the quick install)
4. Select "WSGI" for the framework
5. Python version: 3.10 or higher
6. Click "Next"

## Step 4: Configure Web App

### WSGI Configuration

In the "Web" tab, find the "WSGI configuration file" section and click the link to edit it. Replace the contents with:

```python
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production if not set
if not os.getenv("UPLOAD_DIR"):
    os.environ["UPLOAD_DIR"] = str(project_root / "uploads")
if not os.getenv("UI_PATH"):
    os.environ["UI_PATH"] = str(project_root / "UI_test")

from main import app
```

The WSGI config file path should be: `/var/www/aeroclass_pythonanywhere_com/wsgi.py`

### Virtual Environment

Set the virtual environment path:
- **Virtualenv**: `/var/www/aeroclass_pythonanywhere_com/venv`

### Working Directory

Set the working directory:
- **Working directory**: `/var/www/aeroclass_pythonanywhere_com/9dt_wind_sim`

### Static Files

Add static files mapping:
- **URL directory**: `/ui/`
- **Directory path**: `/var/www/aeroclass_pythonanywhere_com/9dt_wind_sim/UI_test`

### Environment Variables

In the "Web" tab, scroll to "Environment variables" and add:
```
CORS_ORIGINS=https://aeroclass.pythonanywhere.com
```

**Note**: The `asgi.py` file now automatically sets `UPLOAD_DIR` and `UI_PATH` if not provided, so you don't need to set them manually.

## Step 5: Reload Web App

1. Scroll to the top of the "Web" tab
2. Click the big green "Reload" button
3. Check the error logs if the reload fails

## Step 6: Test Deployment

1. Visit your PythonAnywhere URL: `https://aeroclass.pythonanywhere.com`
2. You should see the AeroClass simulator interface
3. Test uploading an STL file
4. Check the API docs at `https://aeroclass.pythonanywhere.com/api/docs`

## Troubleshooting

### 500 Error on Upload

**Problem**: Uploads directory doesn't exist or isn't writable

**Solution**: The `config.py` now automatically creates the uploads directory. If issues persist:
```bash
mkdir -p /var/www/aeroclass_pythonanywhere_com/9dt_wind_sim/uploads
chmod 755 /var/www/aeroclass_pythonanywhere_com/9dt_wind_sim/uploads
```

### Static Files Not Loading

**Problem**: Static files mapping is incorrect

**Solution**: Check the "Static files" section in the Web tab and ensure:
- URL directory: `/ui/`
- Directory path points to the correct `UI_test` folder

### CORS Errors

**Problem**: CORS origins not set correctly

**Solution**: Update environment variables in the Web tab:
```
CORS_ORIGINS=https://aeroclass.pythonanywhere.com
```

### Import Errors

**Problem**: Dependencies not installed

**Solution**: In a Bash console:
```bash
cd /var/www/aeroclass_pythonanywhere_com/9dt_wind_sim
source venv/bin/activate
pip install -r requirements.txt
```

### Application Won't Start

**Problem**: Check the error logs in the Web tab

**Common issues**:
- Missing `asgi.py` file
- Incorrect working directory
- Virtual environment path wrong
- Dependencies not installed

## Limitations

**Current deployment limitations:**
- File storage is temporary (uploads lost on redeploy)
- No database (designs lost on restart)
- No authentication (public access)
- No persistent storage

**For production use**, consider:
- Add PostgreSQL database for persistence
- Use cloud storage (S3/Blob) for STL files
- Add authentication (Auth0/Firebase)
- Set up proper logging and monitoring
- Use a paid PythonAnywhere tier for better performance

## Updating the Application

When you push changes to GitHub:

1. In a Bash console on PythonAnywhere:
```bash
cd /var/www/aeroclass_pythonanywhere_com/9dt_wind_sim
git pull
source venv/bin/activate
pip install -r requirements.txt
```

2. Go to the "Web" tab and click "Reload"

## Monitoring

Check the following regularly:
- **Error logs**: In the Web tab, scroll to "Log files"
- **System resources**: In the "Tasks" tab
- **Disk usage**: In the "Files" tab

## Security Notes

- The `.env` file should never be committed to Git
- Use HTTPS only (PythonAnywhere provides this by default)
- Consider adding rate limiting for API endpoints
- Add authentication before deploying to production

## Support

For issues specific to PythonAnywhere, check:
- [PythonAnywhere documentation](https://help.pythonanywhere.com/)
- [PythonAnywhere forums](https://www.pythonanywhere.com/forums/)

For AeroClass-specific issues, open an issue on GitHub.
