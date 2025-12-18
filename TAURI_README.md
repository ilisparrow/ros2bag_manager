# ROS2 Bag Manager - Tauri Desktop Application

The ROS2 Bag Manager has been configured as a Tauri desktop application, making it shippable as a native Linux application.

## Architecture

```
┌─────────────────────────────────┐
│   Tauri Desktop Application     │
│                                  │
│  ┌────────────────────────────┐ │
│  │  WebView (localhost:8000)  │ │
│  └────────────────────────────┘ │
│               ↓                  │
│  ┌────────────────────────────┐ │
│  │   Rust Backend (Tauri)     │ │
│  │  - Launches Python process │ │
│  │  - Manages lifecycle       │ │
│  │  - System tray integration │ │
│  └────────────────────────────┘ │
│               ↓                  │
│  ┌────────────────────────────┐ │
│  │   Python Backend (FastAPI) │ │
│  │   - Existing app.py        │ │
│  │   - Runs on port 8000      │ │
│  └────────────────────────────┘ │
└─────────────────────────────────┘
```

## Development

### Running in Development Mode

**Option 1: Using the provided script (Recommended)**
```bash
./run_tauri_dev.sh
```

**Option 2: Manual steps**
```bash
# Terminal 1: Start Python backend
python3 app.py

# Terminal 2: Run Tauri (in another terminal)
export PATH="$HOME/.cargo/bin:$PATH"
cargo tauri dev
```

The application will:
1. Start the Python FastAPI backend on port 8000
2. Open a native window with the web interface
3. Connect to localhost:8000

### Development Features

- Hot reload supported (backend changes require manual restart)
- Rust code changes trigger automatic rebuild
- Window size: 1400x900 (configured in `src-tauri/tauri.conf.json`)
- System tray icon (when configured)

## Building for Production

### Create Distributable Packages

```bash
export PATH="$HOME/.cargo/bin:$PATH"
cargo tauri build
```

This will create:
- **DEB package**: `src-tauri/target/release/bundle/deb/ros2-bag-manager_0.1.0_amd64.deb`
- **AppImage**: `src-tauri/target/release/bundle/appimage/ros2-bag-manager_0.1.0_amd64.AppImage`

### Installing the Application

**DEB Package (Debian/Ubuntu)**
```bash
sudo dpkg -i src-tauri/target/release/bundle/deb/ros2-bag-manager_*.deb
```

**AppImage (Universal Linux)**
```bash
chmod +x src-tauri/target/release/bundle/appimage/ros2-bag-manager_*.AppImage
./src-tauri/target/release/bundle/appimage/ros2-bag-manager_*.AppImage
```

## Project Structure

```
rosbag_manager/
├── src-tauri/                  # Tauri Rust application
│   ├── src/
│   │   ├── main.rs            # Entry point
│   │   └── lib.rs             # Main logic (Python backend launcher)
│   ├── Cargo.toml             # Rust dependencies
│   ├── tauri.conf.json        # Tauri configuration
│   └── icons/                 # Application icons
├── app.py                     # FastAPI backend (unchanged)
├── templates/                 # HTML templates (unchanged)
├── scripts/
│   └── start_backend.py       # Python launcher (for sidecar)
└── run_tauri_dev.sh           # Development helper script
```

## Configuration Files

### src-tauri/tauri.conf.json

Key settings:
- `identifier`: `com.rosbag.manager`
- `productName`: `ROS2 Bag Manager`
- `bundle.targets`: `["deb", "appimage"]`
- `app.windows[0]`: Window size and title
- `app.trayIcon`: System tray configuration

### src-tauri/Cargo.toml

Dependencies:
- `tauri`: v2.9.5 (with tray-icon feature)
- `reqwest`: For health-checking the backend
- `tauri-plugin-log`: For logging

## How It Works

1. **Startup**: When you launch the Tauri app, it:
   - Spawns a Python process running `app.py`
   - Waits up to 30 seconds for the backend to be ready (polls localhost:8000)
   - Opens the main window once backend responds

2. **Runtime**:
   - The webview displays the content from localhost:8000
   - All backend functionality (FastAPI) works as before
   - Python process runs as a child of the Tauri process

3. **Shutdown**:
   - When you close the window, Tauri kills the Python backend process
   - Clean shutdown of both processes

## Requirements

### Development
- Rust 1.77.2+ (installed via rustup)
- Tauri CLI 2.x
- Python 3.11+
- ROS2 (for bag operations)
- System dependencies:
  - libwebkit2gtk-4.1-dev
  - libayatana-appindicator3-dev
  - build-essential

### End Users (After Building)
- Python 3.11+
- ROS2 runtime
- 7z (for compression features)

## Troubleshooting

### Backend doesn't start
Check if port 8000 is already in use:
```bash
lsof -i :8000
```

### Window shows blank screen
Ensure Python backend started successfully:
```bash
curl http://localhost:8000
```

### Build fails
Update Rust and Tauri CLI:
```bash
rustup update
cargo install tauri-cli --force
```

## Next Steps

### TODO for Production Release

1. **Add Icon**
   - Create proper icon set in `src-tauri/icons/`
   - Current icons are placeholders

2. **Bundle Python with App**
   - Consider packaging Python runtime with the app
   - Or clearly document Python as a dependency

3. **Add Auto-Updater**
   - Use `tauri-plugin-updater` for automatic updates

4. **Improve Error Handling**
   - Show user-friendly error if backend fails to start
   - Add loading screen during startup

5. **System Tray Menu**
   - Add "Show/Hide", "Quit" menu items
   - Allow running in background

## Building for Other Platforms

### Windows (Cross-compile or build on Windows)
Change `bundle.targets` to include `"msi"` or `"nsis"`

### macOS (Build on macOS)
Change `bundle.targets` to include `"dmg"` or `"app"`

---

For more information:
- Tauri documentation: https://v2.tauri.app/
- FastAPI: https://fastapi.tiangolo.com/
