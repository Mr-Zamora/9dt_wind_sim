# ⚡ Running AeroClass Simulator Locally in the Classroom

This guide explains how to host the AeroClass Aerodynamics Simulator locally on your laptop so an entire classroom of students (30+) can connect, upload STL files, and run simulations simultaneously at lightning speed—**completely free, with zero CPU limits (no tarpit), and no internet latency!**

---

## 📋 Classroom Requirements
1. **Host Laptop:** The teacher's laptop where the AeroClass backend runs.
2. **Local Network:** All student devices (laptops, tablets, or phones) and the host laptop must be connected to the **same school Wi-Fi network**.
3. **Firewall Access:** The host laptop must allow Python to receive incoming network connections.

---

## 🛠️ Step-by-Step Setup Guide

### 1. Find the Host Laptop's Local IP Address
To let the students know where to connect, you need to find your laptop's Wi-Fi IP address:
1. Open **PowerShell** or **Command Prompt** on the host laptop.
2. Type the following command and press Enter:
   ```cmd
   ipconfig
   ```
3. Scroll down to the section named **"Wireless LAN adapter Wi-Fi"** (or similar) and look for the **IPv4 Address**.
   * *Example IPv4 Address: `192.168.1.45` or `10.0.8.12`.* 
4. **Write this IP address down.**

---

### 2. Start the Local AeroClass Server
The backend is pre-configured to bind to `0.0.0.0`, which means it listens to incoming connections from any device on your Wi-Fi network.

1. Open a terminal inside the project folder (`9dt_wind_sim`) on the host laptop.
2. Execute the following command to start the backend:
   ```powershell
   .venv\Scripts\python.exe main.py
   ```
3. The terminal will output:
   `INFO: Uvicorn running on http://0.0.0.0:8000`

> [!IMPORTANT]
> **Windows Defender Firewall Alert:**  
> When you launch the server, Windows will likely display a security popup asking for network permissions.  
> * **Action Required:** Make sure to check **both Private and Public networks**, then click **"Allow Access"**. If you do not do this, Windows will block students from connecting to your laptop.

---

### 3. Have Students Connect in their Browsers
Tell your students to open their web browsers (on their phones, tablets, or laptops connected to the same school Wi-Fi) and type the following address into the address bar:

```http
http://<YOUR-HOST-IP-ADDRESS>:8000/ui/index.html
```

*For example, if your host laptop's local IP address is `192.168.1.45`, they will visit:*  
👉 **`http://192.168.1.45:8000/ui/index.html`**

---

## 🚀 Why This is the Best Classroom Setup

> [!TIP]
> * **Zero Performance Throttling:** Runs directly on your laptop's physical CPU. You will **never** enter the PythonAnywhere "tarpit" limit!
> * **No Disk Space Limits:** Students can upload massive or numerous STL files without worrying about a 512 MB server hosting quota.
> * **Blazing Fast Loads:** Web pages and 3D STL models load instantly (<0.2s) because data travels directly over your local school Wi-Fi network rather than the global internet.
> * **Offline Capable:** Even if the school's external internet connection goes down, as long as the local router remains on, your aerodynamics lab can continue without interruption!
