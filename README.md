# PC Telemetry

A small server that exposes PC metrics (CPU, RAM, disk, network, and
temperatures if LibreHardwareMonitor is running) and streams them over
a WebSocket to an HTML dashboard, viewable from any device with a
browser on the same local network.

## Requirements

- Python 3.9+
- (Optional) [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
  for CPU/GPU temperatures

## Installation

```bash
pip install -r requirements.txt
```

For temperatures, run LibreHardwareMonitor as administrator and enable
`Options` → `Remote Web Server` → `Run` (port 8085 by default).
Everything else works without it — temperatures just show as "--".

## Usage

```bash
python server.py
```

The server prints its local IP on startup. On another device on the
same network, open in a browser:

```
http://PC-IP:8000
```

To add it as a home screen shortcut: browser menu → "Add to Home Screen".

If the viewing device is weaker and the dashboard struggles, increase
`INTERVAL` (seconds between updates) near the top of `server.py`.

## Building standalone executables

```bash
pip install pyinstaller
```

Then either run `build.bat` (Windows) or use
`.github/workflows/build-exe.yml` to build on a GitHub Actions runner.
Both produce two executables in `dist\`:

- **`TelemetriaPC.exe`** — console version. Shows a terminal window
  with logs and the IP address. Useful for debugging.
- **`TelemetriaPCTray.exe`** — background version. No console window;
  runs as a system tray icon instead. Right-click the tray icon for
  the dashboard URL or to quit. This is the one to use day-to-day.

PyInstaller `--onefile` executables are sometimes flagged by antivirus
software as a false positive (due to self-extracting into a temp
folder on startup). It's not malware — just allow it to run or add an
exclusion.

## Running automatically on startup

**TelemetriaPCTray.exe** — press `Win + R`, type `shell:startup`, press
Enter. This opens your personal Startup folder. Create a shortcut to
`TelemetriaPCTray.exe` there (right-click the exe → Send to → Desktop,
then drag that shortcut into the Startup folder, or hold Alt while
dragging the exe directly into the folder). It will now start silently
in the tray every time you log in.

**LibreHardwareMonitor** — it has this built in:
`Options` → `Start Minimized`, `Options` → `Minimize On Close`. For
`Options` → `Run On Windows Startup`, note that it needs administrator
rights to read sensors, and the built-in startup option does not
launch elevated — temperatures may end up missing after a reboot. The
reliable way is Task Scheduler:


## Notes

Sensor names in LibreHardwareMonitor vary by hardware. If temperatures
don't show up, check the names at `http://localhost:8085/data.json`
and adjust the keywords in `read_hardware_sensors()` in `server.py`.
