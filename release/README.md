# ROS2 Bag Manager - Tauri Desktop Application

## ⚠️ IMPORTANT WARNING ⚠️

**THIS RELEASE WAS NOT ONLY VIBECODED BUT I NEVER USED TAURI ON MY OWN. PLEASE BE CAREFUL!**

This is an experimental desktop application version of the ROS2 Bag Manager, packaged as a Tauri AppImage. While it has been tested and appears to work, it was developed entirely through AI assistance without prior Tauri experience.

**Use at your own risk. Test thoroughly before using with important data.**

## What is this?

A shippable desktop application that bundles:
- FastAPI Python backend
- HTMX web frontend
- Automatic dependency management via `uv`
- ROS2 integration for bag playback/recording

## Requirements

- Linux x86_64
- ROS2 installation (tested with ROS2 Rolling)
- `uv` package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- System ROS2 environment sourced

## How to Run

1. Make the AppImage executable:
```bash
chmod +x "ROS2 Bag Manager_0.1.0_amd64.AppImage"
```

2. Run it:
```bash
./ROS2\ Bag\ Manager_0.1.0_amd64.AppImage
```

3. On first launch:
   - The app will create a Python virtual environment in `/tmp/rosbag_manager_venv`
   - Dependencies will be automatically installed (takes ~20 seconds)
   - A window will open showing the ROS2 Bag Manager interface

4. Use the folder browser or enter a path manually when prompted

## Known Issues

- File browser dialog may not work (will show manual input dialog as fallback)
- Recording list refresh has a 1-second delay
- Large file (80MB) - consider using Git LFS if contributing
- First launch is slower due to dependency installation

## Features

- Browse and manage ROS2 bag files
- Play bags with speed control and loop mode
- Record new bags with topic selection
- Tag and organize bags
- Compress bags to .7z format
- QoS policy configuration per topic
- Mobile-responsive interface

## Technical Details

- **Framework**: Tauri v2 (Rust + WebView)
- **Backend**: Python 3.12 with FastAPI
- **Frontend**: HTMX + Jinja2 templates
- **Package Manager**: uv with `--system-site-packages` for ROS2 access
- **Distribution**: AppImage (single-file executable)

## Troubleshooting

If the app doesn't start:
1. Check that ROS2 is sourced: `echo $ROS_DISTRO`
2. Verify `uv` is installed: `which uv`
3. Check logs in terminal where you launched the AppImage
4. Try removing the venv: `rm -rf /tmp/rosbag_manager_venv`

## Building from Source

See the `tauri-integration` branch for build instructions and source code.
