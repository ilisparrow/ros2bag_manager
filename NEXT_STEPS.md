# Next Steps for Tauri Integration

## Current Progress

✅ Rust/Cargo installed (1.92.0)
✅ Tauri dependencies verified
✅ Python launcher script created (`scripts/start_backend.py`)
✅ Implementation plan documented (`TAURI_IMPLEMENTATION.md`)
🔄 Tauri CLI installing in background...

## Once Tauri CLI Installation Completes

### 1. Initialize Tauri Project
```bash
source $HOME/.cargo/env
cargo tauri init
```

Answer the prompts:
- App name: `ROS2 Bag Manager`
- Window title: `ROS2 Bag Manager`
- Web assets location: `.` (current directory)
- Dev server URL: `http://localhost:8000`
- Frontend dev command: Leave empty (we'll start Python manually)
- Frontend build command: Leave empty

### 2. Configure tauri.conf.json

Key changes needed:
- Add sidecar configuration for Python backend
- Configure window properties
- Add system tray support
- Set bundle options

### 3. Create main.rs Logic

The Rust code needs to:
- Launch Python backend as subprocess
- Wait for server to be ready (poll http://localhost:8000)
- Show loading splash while waiting
- Open main window when ready
- Handle graceful shutdown

### 4. Test Development Build

```bash
# Terminal 1: Start Python backend manually first time
python app.py

# Terminal 2: Run Tauri in dev mode
cargo tauri dev
```

### 5. Create Production Build

```bash
cargo tauri build --bundles deb,appimage
```

Output will be in: `src-tauri/target/release/bundle/`

## Alternative If Tauri Is Too Complex

We can instead create a simpler Docker-based solution:

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y python3 ros-jazzy-desktop
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python3", "app.py"]
```

User would run:
```bash
docker run -p 8000:8000 -v ~/rosbags:/rosbags rosbag-manager
```

Then access via browser at `localhost:8000`.

## Decision Point

After seeing Tauri complexity, we can decide:
1. **Continue with Tauri** → Native desktop app, better UX
2. **Switch to Docker** → Simpler, faster to ship, still portable

Both are valid approaches depending on priority (native feel vs. simplicity).
