"""
PC Telemetry - server
----------------------
Reads PC metrics (CPU, RAM, disk, network and, if available,
temperatures via LibreHardwareMonitor) and streams them over a
WebSocket to any device on the local network running just a browser.

Usage:
    pip install -r requirements.txt
    python server.py

Then open on another device: http://<PC-IP>:8000
"""

import asyncio
import os
import re
import socket
import sys
import time

import psutil
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

# --- Configuration -------------------------------------------------------

INTERVAL = 1.0          # seconds between updates (increase if the client struggles)
LHM_URL = "http://localhost:8085/data.json"  # LibreHardwareMonitor Remote Web Server
LHM_TIMEOUT = 0.4

# When packaged with PyInstaller (--onefile), static files are
# extracted to a temp folder accessible via sys._MEIPASS.
# In normal mode (python server.py), use the folder next to this file.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS  # type: ignore[attr-defined]
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI()


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(STATIC_DIR, "manifest.json"))


@app.get("/icon.svg")
async def icon():
    return FileResponse(os.path.join(STATIC_DIR, "icon.svg"))


# --- Sensors (LibreHardwareMonitor, optional) -----------------------------

def _parse_float(text):
    m = re.search(r"[-+]?\d*\.?\d+", text or "")
    return float(m.group()) if m else None


def _fetch_lhm_tree():
    try:
        r = requests.get(LHM_URL, timeout=LHM_TIMEOUT)
        return r.json()
    except Exception:
        return None


def _flatten_lhm(tree):
    """Groups sensors by category (Temperatures, Load, ...)."""
    flat = {}

    def walk(node, group=None):
        text = node.get("Text", "")
        children = node.get("Children") or []
        if not children and "Value" in node and group:
            flat.setdefault(group, []).append((text, node["Value"]))
        for c in children:
            new_group = text if text in (
                "Temperatures", "Load", "Powers", "Clocks", "Fans", "Voltages"
            ) else group
            walk(c, new_group)

    for child in tree.get("Children", []):
        walk(child)
    return flat


def read_hardware_sensors():
    """Returns (cpu_temp, gpu_temp, gpu_load) or (None, None, None)."""
    tree = _fetch_lhm_tree()
    if not tree:
        return None, None, None

    flat = _flatten_lhm(tree)
    cpu_temp = gpu_temp = gpu_load = None

    for name, val in flat.get("Temperatures", []):
        low = name.lower()
        if cpu_temp is None and ("cpu package" in low or "tctl" in low):
            cpu_temp = _parse_float(val)
        if gpu_temp is None and "gpu" in low and "hot spot" not in low:
            gpu_temp = _parse_float(val)

    for name, val in flat.get("Load", []):
        if gpu_load is None and "gpu core" in name.lower():
            gpu_load = _parse_float(val)

    return cpu_temp, gpu_temp, gpu_load


def disk_root():
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + "\\"
    return "/"


# --- WebSocket -------------------------------------------------------------

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()

    psutil.cpu_percent(interval=None, percpu=True)  # prime the counter
    prev_net = psutil.net_io_counters()
    prev_t = time.time()
    root = disk_root()

    try:
        while True:
            await asyncio.sleep(INTERVAL)

            cores = psutil.cpu_percent(interval=None, percpu=True)
            cpu_total = sum(cores) / len(cores) if cores else 0.0
            ram_pct = psutil.virtual_memory().percent
            disk_pct = psutil.disk_usage(root).percent

            net = psutil.net_io_counters()
            now = time.time()
            dt = max(now - prev_t, 0.001)
            up_kbps = (net.bytes_sent - prev_net.bytes_sent) / 1024 / dt
            down_kbps = (net.bytes_recv - prev_net.bytes_recv) / 1024 / dt
            prev_net, prev_t = net, now

            cpu_temp, gpu_temp, gpu_load = read_hardware_sensors()

            await websocket.send_json({
                "cpu": round(cpu_total, 1),
                "cores": [round(c, 1) for c in cores],
                "ram": round(ram_pct, 1),
                "disk": round(disk_pct, 1),
                "net_up": round(up_kbps, 1),
                "net_down": round(down_kbps, 1),
                "cpu_temp": cpu_temp,
                "gpu_temp": gpu_temp,
                "gpu_load": gpu_load,
            })
    except WebSocketDisconnect:
        pass


def get_lan_ip():
    """Best-effort way to find the local network IP (no real traffic sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    import uvicorn

    ip = get_lan_ip()
    print("=" * 50)
    print("  PC TELEMETRY")
    print("=" * 50)
    print(f"  Open on another device:  http://{ip}:8000")
    print("  (it must be on the same Wi-Fi network)")
    print("  To stop: close this window or press Ctrl+C")
    print("=" * 50)

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    except KeyboardInterrupt:
        print("\nServer stopped.")
