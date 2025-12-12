from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
from datetime import datetime
from typing import Optional
import subprocess
import os
import tkinter as tk
from tkinter import filedialog

app = FastAPI(title="ROS2 Bag Manager")

templates = Jinja2Templates(directory="templates")

METADATA_FILE = "bags_metadata.json"
CONFIG_FILE = "config.json"
BAGS_FOLDER = None


def load_config():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_metadata():
    if Path(METADATA_FILE).exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def get_bag_info(bag_path: str):
    try:
        result = subprocess.run(
            ['ros2', 'bag', 'info', bag_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        info = {
            'path': bag_path,
            'exists': True,
            'topics': [],
            'duration': '',
            'messages': 0,
            'size': 0
        }

        if result.returncode == 0:
            output = result.stdout

            for line in output.split('\n'):
                if 'Topic:' in line or 'topic:' in line.lower():
                    parts = line.split('|')
                    if len(parts) >= 2:
                        topic_name = parts[0].strip().split(':')[-1].strip()
                        info['topics'].append(topic_name)
                elif 'Duration:' in line:
                    info['duration'] = line.split(':')[-1].strip()
                elif 'messages' in line.lower():
                    try:
                        info['messages'] = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass

        path_obj = Path(bag_path)
        if path_obj.exists():
            info['size'] = sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file())

        return info
    except Exception as e:
        return {
            'path': bag_path,
            'exists': False,
            'error': str(e),
            'topics': [],
            'duration': '',
            'messages': 0,
            'size': 0
        }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    metadata = load_metadata()
    config = load_config()
    bags = metadata.get('bags', [])
    current_folder = config.get('last_folder', '')

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "bags": bags, "current_folder": current_folder}
    )


def get_available_topics():
    try:
        result = subprocess.run(
            ['ros2', 'topic', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            topics = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return topics
        return []
    except Exception as e:
        print(f"Error getting topics: {e}")
        return []


@app.get("/browse-folder")
async def browse_folder():
    config = load_config()
    initial_dir = config.get('last_folder', str(Path.home()))

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    folder = filedialog.askdirectory(
        title="Select ROS2 Bags Folder",
        initialdir=initial_dir
    )

    root.destroy()

    if folder:
        config['last_folder'] = folder
        save_config(config)
        return JSONResponse({"folder": folder})
    else:
        raise HTTPException(status_code=400, detail="No folder selected")


@app.get("/available-topics")
async def available_topics():
    topics = get_available_topics()
    return JSONResponse({"topics": topics})


@app.post("/set-folder")
async def set_folder(folder: str = Form(...)):
    global BAGS_FOLDER
    BAGS_FOLDER = folder

    config = load_config()
    config['last_folder'] = folder
    save_config(config)

    metadata = load_metadata()
    metadata['folder'] = folder

    bags = []
    folder_path = Path(folder)

    if folder_path.exists() and folder_path.is_dir():
        for item in folder_path.iterdir():
            if item.is_dir():
                db3_files = list(item.rglob('*.db3'))
                mcap_files = list(item.rglob('*.mcap'))
                bag_files = db3_files + mcap_files

                if bag_files:
                    file_type = 'db3' if db3_files else 'mcap'
                    print(f"Found bag: {item.name} with {len(bag_files)} {file_type} files")
                    bag_info = get_bag_info(str(item))
                    bag_data = {
                        'name': item.name,
                        'path': str(item),
                        'date': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        'size': bag_info['size'],
                        'topics': bag_info['topics'],
                        'duration': bag_info['duration'],
                        'messages': bag_info['messages'],
                        'format': file_type
                    }
                    bags.append(bag_data)
                else:
                    print(f"Skipping {item.name} - no bag files found")

    print(f"Total bags found: {len(bags)}")
    bags.sort(key=lambda x: x['date'], reverse=True)
    metadata['bags'] = bags
    save_metadata(metadata)

    return templates.TemplateResponse(
        "bag_list.html",
        {"request": Request(scope={'type': 'http'}), "bags": bags}
    )


@app.get("/bag-info/{bag_index}")
async def get_bag_info_endpoint(request: Request, bag_index: int):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    bag = bags[bag_index]
    return templates.TemplateResponse(
        "bag_info.html",
        {"request": request, "bag": bag, "bag_index": bag_index}
    )


@app.post("/play-bag")
async def play_bag(
    bag_index: int = Form(...),
    rate: float = Form(1.0),
    loop: bool = Form(False)
):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    bag = bags[bag_index]
    bag_path = bag['path']

    cmd = ['ros2', 'bag', 'play', bag_path, '-r', str(rate)]
    if loop:
        cmd.append('--loop')

    try:
        subprocess.Popen(cmd)
        return JSONResponse({"status": "Playing", "bag": bag['name'], "rate": rate, "loop": loop})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/record-bag")
async def record_bag(
    bag_name: str = Form(...),
    duration: Optional[int] = Form(None),
    topics: Optional[str] = Form(None)
):
    config = load_config()
    folder = config.get('last_folder', '.')

    bag_path = Path(folder) / bag_name

    cmd = ['ros2', 'bag', 'record', '-o', str(bag_path)]

    if topics:
        topic_list = [t.strip() for t in topics.split(',')]
        cmd.extend(topic_list)
    else:
        cmd.append('-a')

    if duration:
        cmd.extend(['--duration', str(duration)])

    try:
        subprocess.Popen(cmd)
        return JSONResponse({
            "status": "Recording started",
            "bag_name": bag_name,
            "duration": duration,
            "topics": topics or "all"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compress-bag")
async def compress_bag(bag_index: int = Form(...)):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    bag = bags[bag_index]
    bag_path = Path(bag['path'])
    compressed_path = bag_path.with_suffix('.7z')

    try:
        cmd = ['7z', 'a', str(compressed_path), str(bag_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return JSONResponse({
                "status": "Compressed",
                "original": str(bag_path),
                "compressed": str(compressed_path)
            })
        else:
            raise HTTPException(status_code=500, detail="Compression failed")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="7z not found. Please install p7zip-full")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
