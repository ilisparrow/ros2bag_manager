# ROS2 Bag Manager

A simple, web-based tool for managing ROS2 bag files. Built with FastAPI and HTMX for a clean, responsive interface.

## Features

- Browse and load ROS2 bags from a folder
- View bag metadata (date, size, topics, duration, message count)
- Metadata stored in JSON format
- Play bags with adjustable speed (0.5x to 10x)
- Loop playback support
- Record new bags with optional time limits
- Record specific topics or all topics
- Compress bags using 7z format
- Simple, KISS interface

## Requirements

- Python 3.11+
- ROS2 (any distribution)
- 7z (p7zip-full) for compression

## Installation

1. Install system dependencies:
```bash
sudo apt install p7zip-full
```

2. Install Python dependencies:
```bash
pip install -e .
```

Or install manually:
```bash
pip install fastapi uvicorn jinja2 python-multipart aiofiles
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Click "Browse" to select your bags folder (or type the path manually)
   - Your folder selection is saved between sessions

4. Click "Load Bags" to scan the folder for ROS2 bags

5. Select a bag from the list to view details

6. Use the controls to:
   - Play bags with different speeds
   - Enable loop playback
   - Compress bags
   - Record new bags

## Features in Detail

### Bag Selection
- Click "Browse" to open a folder selection dialog
- The selected folder path is automatically saved and restored on next launch
- All bags are loaded and displayed with date and size
- Click on any bag to view detailed information

### Bag Information
- Path, date, and size
- Duration and message count
- List of all topics in the bag

### Playback Controls
- Adjustable playback speed (0.5x, 1x, 2x, 5x, 10x)
- Loop mode for continuous playback
- One-click play button

### Recording
- Record new bags with custom names
- Optional duration limit (in seconds)
- Record all topics or specific comma-separated topics
- Bags saved to the currently selected folder

### Compression
- Compress bags to 7z format with one click
- Useful for archiving or saving space

## File Structure

```
rosbag_manager/
├── app.py                  # Main FastAPI application
├── templates/
│   ├── index.html         # Main page template
│   ├── bag_list.html      # Bag list component
│   └── bag_info.html      # Bag info component
├── bags_metadata.json     # Auto-generated metadata file
└── README.md
```

## Notes

- Metadata is automatically saved to `bags_metadata.json`
- User preferences (last folder) are saved to `config.json`
- The server runs on port 8000 by default
- Bag playback and recording run in separate processes
- Compressed files are saved with .7z extension in the same directory
- The folder browser uses tkinter, which should be included with Python

