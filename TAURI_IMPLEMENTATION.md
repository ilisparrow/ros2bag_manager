# Tauri Implementation Plan

## Overview
Convert ROS2 Bag Manager to a shippable desktop application using Tauri with Python FastAPI backend as a sidecar process.

## Architecture

```
┌─────────────────────────────────────┐
│         Tauri Application           │
│  ┌───────────────────────────────┐ │
│  │   Webview (localhost:8000)    │ │
│  └───────────────────────────────┘ │
│               ↓                     │
│  ┌───────────────────────────────┐ │
│  │   Rust Backend (Tauri Core)   │ │
│  │   - Launches Python sidecar   │ │
│  │   - Manages process lifecycle │ │
│  │   - System tray integration   │ │
│  └───────────────────────────────┘ │
│               ↓                     │
│  ┌───────────────────────────────┐ │
│  │  Python Sidecar (FastAPI)     │ │
│  │  - Existing app.py unchanged  │ │
│  │  - Runs on localhost:8000     │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Tauri Setup
1. Initialize Tauri project in repository
2. Configure `tauri.conf.json` with app metadata
3. Set up development environment

### Phase 2: Python Sidecar Configuration
1. Bundle Python script as sidecar
2. Configure sidecar in `tauri.conf.json`
3. Create launcher script for Python backend
4. Handle port availability and startup

### Phase 3: Window & Webview Setup
1. Configure window size and properties
2. Set webview to load `http://localhost:8000`
3. Add loading screen while backend starts
4. Handle backend connection errors

### Phase 4: System Integration
1. Add system tray icon
2. Create tray menu (Show/Hide/Quit)
3. Handle window close behavior (minimize to tray)
4. Auto-start backend on app launch

### Phase 5: Build & Packaging
1. Create build configuration for Linux
2. Generate `.deb` and `.AppImage` packages
3. Add app icon and metadata
4. Test installation process

## File Structure

```
rosbag_manager/
├── src-tauri/
│   ├── Cargo.toml              # Rust dependencies
│   ├── tauri.conf.json         # Tauri configuration
│   ├── build.rs                # Build script
│   ├── icons/                  # App icons
│   └── src/
│       └── main.rs             # Tauri main application
├── app.py                      # FastAPI backend (unchanged)
├── templates/                  # HTML templates (unchanged)
├── requirements.txt            # Python dependencies
└── scripts/
    └── start_backend.py        # Python launcher for Tauri
```

## Key Configurations

### tauri.conf.json (Essential Parts)
```json
{
  "productName": "ROS2 Bag Manager",
  "identifier": "com.rosbag.manager",
  "bundle": {
    "active": true,
    "targets": ["deb", "appimage"],
    "externalBin": ["scripts/start_backend"],
    "icon": ["icons/icon.png"]
  },
  "windows": [{
    "title": "ROS2 Bag Manager",
    "width": 1400,
    "height": 900,
    "url": "http://localhost:8000"
  }],
  "systemTray": {
    "iconPath": "icons/icon.png"
  }
}
```

### main.rs (Core Logic)
- Launch Python backend as child process
- Wait for server to be ready (poll localhost:8000)
- Show loading window
- Switch to main window when ready
- Handle cleanup on exit

## Dependencies

### System Requirements (already installed)
- libwebkit2gtk-4.1-dev
- libayatana-appindicator3-dev
- build-essential

### Rust Dependencies (Cargo.toml)
- tauri = "2.x"
- serde_json
- reqwest (for health checks)

### Python Dependencies (existing)
- fastapi
- uvicorn
- jinja2
- python-multipart
- aiofiles

## Build Commands

### Development
```bash
cargo tauri dev
```

### Production Build
```bash
cargo tauri build --bundles deb,appimage
```

## Advantages

1. **No Code Changes**: Existing Python/FastAPI code remains untouched
2. **Native Experience**: System tray, native menus, desktop integration
3. **Cross-Platform**: Can build for Linux, Windows, macOS
4. **Small Size**: ~15-20MB app + Python runtime
5. **Auto-Updates**: Can add Tauri updater plugin later
6. **Native File Dialogs**: Replace tkinter with Tauri's native dialogs
7. **Background Running**: App can run in system tray

## Distribution

### Linux Packages
- **.deb**: For Debian/Ubuntu users (`sudo dpkg -i rosbag-manager.deb`)
- **.AppImage**: Universal Linux binary (chmod +x and run)
- **Snap/Flatpak**: Can be added later

### Requirements for End Users
- ROS2 installed (runtime requirement)
- Python 3.11+ (or bundle Python with app)
- 7z for compression features

## Next Steps

1. Complete Rust/Tauri installation
2. Run `cargo tauri init` to scaffold project
3. Configure sidecar for Python backend
4. Test development build
5. Create production build script
6. Generate installers

## Alternative: Docker Approach

If Tauri proves complex, alternative is Docker:
- Package everything in container
- Expose web UI on localhost
- User runs: `docker run -p 8000:8000 rosbag-manager`
- Simpler but less native feel
