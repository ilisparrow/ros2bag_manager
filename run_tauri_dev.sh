#!/bin/bash

# Script to run Tauri in development mode
# This starts the Python backend first, then launches Tauri

echo "Starting Python backend..."
python3 app.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

echo "Launching Tauri..."
export PATH="$HOME/.cargo/bin:$PATH"
cargo tauri dev

# Cleanup
echo "Stopping backend..."
kill $BACKEND_PID 2>/dev/null
