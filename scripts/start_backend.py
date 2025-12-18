#!/usr/bin/env python3
"""
Backend launcher for Tauri sidecar.
This script starts the FastAPI server for the ROS2 Bag Manager.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

if __name__ == "__main__":
    import uvicorn
    from app import app

    # Run uvicorn server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
