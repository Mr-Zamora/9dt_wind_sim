# PythonAnywhere Free-Tier Deployment Guide (Native ASGI)

This guide explains how to deploy **AeroClass** to PythonAnywhere's free tier with the **full 3D physics and aerodynamic calculations active**, while safely staying well under the 512 MB disk space quota.

---

## Prerequisites

1. **PythonAnywhere Account:** A free-tier account (e.g., username `aeroclass`).
2. **API Token Generation:**
   - Log into PythonAnywhere and navigate to: `https://www.pythonanywhere.com/user/YOUR_USERNAME/account/` (replace `YOUR_USERNAME` with your actual username).
   - Go to the **API Token** tab.
   - Click the button that says **Create a new API token**.
   - *Note: After creating the token, you must open a **new Bash console** for the environment to automatically load the `$API_TOKEN` variable used by the `pa` command-line tool.*

---

## Step 1: Clone the Repository

1. Log in to PythonAnywhere.
2. Go to the **Consoles** tab and start a new **Bash** console.
3. Clone your repository:
   ```bash
   git clone https://github.com/Mr-Zamora/9dt_wind_sim.git
   cd 9dt_wind_sim
   ```

---

## Step 2: Create a Lightweight Virtual Environment

To prevent hitting the 512 MB disk space limit while keeping the full physics suite (NumPy and SciPy) active:

1. **Clean up any accidental pip installer cache:**
   ```bash
   rm -rf ~/.cache/pip
   ```
2. **Create the virtualenv inheriting the pre-installed system packages:**
   *PythonAnywhere already has NumPy and SciPy pre-installed globally. By using `--system-site-packages`, your environment reuses them instantly at zero disk space cost.*
   ```bash
   # Create a 3.10 virtual environment inheriting system libraries
   python3.10 -m venv --system-site-packages venv
   
   # Activate the environment
   source venv/bin/activate
   ```
3. **Upgrade pip and install remaining dependencies without caching:**
   *Using `--no-cache-dir` prevents pip from downloading and keeping duplicate compressed `.whl` files on your disk.*
   ```bash
   # Upgrade pip cleanly
   pip install --no-cache-dir --upgrade pip
   
   # Install FastAPI, Trimesh, a2wsgi, and others
   pip install --no-cache-dir -r requirements.txt
   ```

---

## Step 3: Delete Incompatible WSGI Setup (If applicable)

> [!IMPORTANT]
> **Why we do not use the standard WSGI Web App Tab:**
> PythonAnywhere disables Python threading GIL-switching in standard WSGI web applications. Frameworks like FastAPI wrapped with `a2wsgi` rely on a background event-loop thread. If deployed as a WSGI app, the background thread **never runs**, resulting in an infinite deadlock and a `499` (Client Closed Connection) timeout from Nginx.

If you already created a standard WSGI app on your domain, delete it from your terminal:
```bash
pa webapp delete --domain 'yourusername.pythonanywhere.com'
```

---

## Step 4: Create a Native ASGI Web Application

Deploy FastAPI natively using PythonAnywhere's experimental ASGI support. This runs Uvicorn directly on the main thread, bypassing all threading deadlocks!

Run this in your **new Bash console** (where your newly created API token is automatically active):

```bash
pa website create --domain 'yourusername.pythonanywhere.com' --command '/home/yourusername/9dt_wind_sim/venv/bin/uvicorn --app-dir /home/yourusername/9dt_wind_sim --uds ${DOMAIN_SOCKET} main:app'
```

*Replace `yourusername` with your actual PythonAnywhere username.*

### Note on Path Integrity
All configurations in `config.py` resolve **absolutely** relative to the project root directory. Uvicorn will automatically find the `UI_test` folder, serving the simulator static assets under the `/ui` path with no additional configuration required.

---

## Step 5: Test and Verify

1. Open your browser and navigate to `https://yourusername.pythonanywhere.com/`.
2. You will be automatically redirected to `https://yourusername.pythonanywhere.com/ui/index.html`.
3. The interactive **3D Aerodynamic Simulator** will load. Try uploading an `.stl` design to verify the calculation engine and streamline visualizations.

---

## Maintenance & Updates

### How to Pull Code Updates
When you push new changes to GitHub, run the following in your PythonAnywhere Bash console:
```bash
# Navigate to project folder
cd ~/9dt_wind_sim

# Pull latest commits
git pull

# Reload website to apply changes
pa website reload --domain 'yourusername.pythonanywhere.com'
```

### Self-Cleaning Uploads Directory
The server is equipped with a self-healing **request-time uploads cleanup utility**. Every time an STL file is uploaded, the server automatically sweeps the `uploads/` folder and deletes any `.stl` files older than **2 hours**. No manual server maintenance or cron jobs are required to protect your 512 MB disk space!

### Log Locations
If you need to debug or check server statistics:
* **Server log:** `/var/log/yourusername.pythonanywhere.com.server.log`
* **Access log:** `/var/log/yourusername.pythonanywhere.com.access.log`
