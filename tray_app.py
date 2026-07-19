"""
PC Telemetry - system tray launcher
-------------------------------------
Runs the server silently in the background with a small system tray
icon (no console window). Right-click the tray icon to open the
dashboard or quit.
"""

import os
import sys
import threading
import traceback
import webbrowser

import pystray
import uvicorn
from PIL import Image, ImageDraw

from server import app, get_lan_ip

PORT = 8000


def build_icon_image():
    """Draws a small gauge-style icon without needing any external image file."""
    size = 64
    img = Image.new("RGBA", (size, size), (12, 15, 18, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((6, 6, size - 6, size - 6), outline=(35, 40, 48, 255), width=4)
    draw.line((size / 2, size / 2, size - 14, 18), fill=(255, 159, 28, 255), width=5)
    draw.ellipse(
        (size / 2 - 5, size / 2 - 5, size / 2 + 5, size / 2 + 5),
        fill=(255, 159, 28, 255),
    )
    return img


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


def main():
    threading.Thread(target=run_server, daemon=True).start()

    ip = get_lan_ip()
    url = f"http://{ip}:{PORT}"

    def open_dashboard(icon, item):
        webbrowser.open(url)

    def quit_app(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(url, None, enabled=False),
        pystray.MenuItem("Open dashboard", open_dashboard, default=True),
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("pc_telemetry", build_icon_image(), "PC Telemetry", menu)
    icon.run()


def _log_path():
    base = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    return os.path.join(base, "tray_error.log")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # No console in windowed mode, so write failures to a log file
        # instead of losing them silently.
        with open(_log_path(), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
