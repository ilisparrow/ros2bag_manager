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
RECORDING_PROCESS = None
PLAYBACK_PROCESS = None
PLAYBACK_BAG_NAME = None


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
    current_user = config.get('last_user', '')

    return templates.TemplateResponse(
        "index_new.html",
        {"request": request, "bags": bags, "current_folder": current_folder, "current_user": current_user}
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

    try:
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
    except Exception as e:
        # If tkinter fails (e.g., in AppImage), return error so UI can fallback to manual entry
        raise HTTPException(status_code=500, detail=f"File dialog failed: {str(e)}")


@app.post("/set-folder")
async def set_folder(folder_path: str = Form(...)):
    """Set folder path manually (fallback when file dialog doesn't work)"""
    folder = Path(folder_path).expanduser()

    if not folder.exists():
        raise HTTPException(status_code=400, detail="Folder does not exist")

    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    config = load_config()
    config['last_folder'] = str(folder)
    save_config(config)

    return JSONResponse({"folder": str(folder)})


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

    # Create a map of existing bags by path to preserve metadata
    existing_bags_map = {}
    if 'bags' in metadata:
        for bag in metadata['bags']:
            existing_bags_map[bag['path']] = bag

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
                    bag_path = str(item)

                    # Check if we have existing metadata for this bag
                    if bag_path in existing_bags_map:
                        # Update the existing bag data with fresh info
                        bag_data = existing_bags_map[bag_path]
                        bag_data.update({
                            'name': item.name,
                            'date': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                            'size': bag_info['size'],
                            'topics': bag_info['topics'],
                            'duration': bag_info['duration'],
                            'messages': bag_info['messages'],
                            'format': file_type
                        })
                        # Preserve 'tags' and 'qos_settings' if they exist
                    else:
                        # Create new bag data
                        bag_data = {
                            'name': item.name,
                            'path': bag_path,
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
        "bag_info_updated.html",
        {"request": request, "bag": bag, "bag_index": bag_index}
    )


@app.get("/bags_metadata.json")
async def get_metadata_json():
    metadata = load_metadata()
    return JSONResponse(metadata)


@app.post("/set-user")
async def set_user(user: str = Form(...)):
    config = load_config()
    config['last_user'] = user
    save_config(config)
    return JSONResponse({"status": "ok"})


@app.post("/play-bag")
async def play_bag(
    bag_index: int = Form(...),
    rate: float = Form(1.0),
    loop: bool = Form(False)
):
    global PLAYBACK_PROCESS, PLAYBACK_BAG_NAME

    if PLAYBACK_PROCESS and PLAYBACK_PROCESS.poll() is None:
        raise HTTPException(status_code=400, detail="Playback already in progress")

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
        PLAYBACK_PROCESS = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        PLAYBACK_BAG_NAME = bag['name']
        return JSONResponse({"status": "Playing", "bag": bag['name'], "rate": rate, "loop": loop})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-playback")
async def stop_playback():
    global PLAYBACK_PROCESS, PLAYBACK_BAG_NAME

    if PLAYBACK_PROCESS is None or PLAYBACK_PROCESS.poll() is not None:
        raise HTTPException(status_code=400, detail="No playback in progress")

    try:
        PLAYBACK_PROCESS.terminate()
        PLAYBACK_PROCESS.wait(timeout=5)
        bag_name = PLAYBACK_BAG_NAME
        PLAYBACK_PROCESS = None
        PLAYBACK_BAG_NAME = None
        return JSONResponse({"status": "Playback stopped", "bag": bag_name})
    except Exception as e:
        PLAYBACK_PROCESS.kill()
        PLAYBACK_PROCESS = None
        PLAYBACK_BAG_NAME = None
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/playback-status")
async def playback_status():
    global PLAYBACK_PROCESS, PLAYBACK_BAG_NAME

    if PLAYBACK_PROCESS is None:
        return JSONResponse({"playing": False})

    if PLAYBACK_PROCESS.poll() is None:
        return JSONResponse({"playing": True, "bag": PLAYBACK_BAG_NAME})
    else:
        PLAYBACK_PROCESS = None
        PLAYBACK_BAG_NAME = None
        return JSONResponse({"playing": False})


@app.get("/playback-output")
async def playback_output():
    global PLAYBACK_PROCESS

    if PLAYBACK_PROCESS is None or PLAYBACK_PROCESS.stdout is None:
        return JSONResponse({"output": ""})

    try:
        import select
        if select.select([PLAYBACK_PROCESS.stdout], [], [], 0)[0]:
            line = PLAYBACK_PROCESS.stdout.readline()
            return JSONResponse({"output": line})
        return JSONResponse({"output": ""})
    except:
        return JSONResponse({"output": ""})


@app.post("/rename-bag")
async def rename_bag(bag_index: int = Form(...), new_name: str = Form(...)):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    bag = bags[bag_index]
    old_path = Path(bag['path'])
    new_path = old_path.parent / new_name

    try:
        old_path.rename(new_path)
        bags[bag_index]['name'] = new_name
        bags[bag_index]['path'] = str(new_path)
        metadata['bags'] = bags
        save_metadata(metadata)
        return JSONResponse({"status": "Renamed", "new_name": new_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete-bag")
async def delete_bag(bag_index: int = Form(...)):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    bag = bags[bag_index]
    bag_path = Path(bag['path'])

    try:
        import shutil
        if bag_path.exists():
            shutil.rmtree(bag_path)
        bags.pop(bag_index)
        metadata['bags'] = bags
        save_metadata(metadata)
        return JSONResponse({"status": "Deleted", "name": bag['name']})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-bag-tag")
async def add_bag_tag(bag_index: int = Form(...), tag: str = Form(...)):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    if 'tags' not in bags[bag_index]:
        bags[bag_index]['tags'] = []

    # Don't add duplicate tags
    if tag not in bags[bag_index]['tags']:
        bags[bag_index]['tags'].append(tag)

    metadata['bags'] = bags
    save_metadata(metadata)
    return JSONResponse({"status": "Tag added", "tag": tag})


@app.post("/remove-bag-tag")
async def remove_bag_tag(bag_index: int = Form(...), tag: str = Form(...)):
    metadata = load_metadata()
    bags = metadata.get('bags', [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    if 'tags' in bags[bag_index] and tag in bags[bag_index]['tags']:
        bags[bag_index]['tags'].remove(tag)
        metadata['bags'] = bags
        save_metadata(metadata)
        return JSONResponse({"status": "Tag removed", "tag": tag})
    else:
        raise HTTPException(status_code=404, detail="Tag not found")


@app.post("/record-bag")
async def record_bag(
    bag_name: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    topics: Optional[str] = Form(None),
    user: Optional[str] = Form(None)
):
    global RECORDING_PROCESS

    if RECORDING_PROCESS and RECORDING_PROCESS.poll() is None:
        raise HTTPException(status_code=400, detail="Recording already in progress")

    config = load_config()
    folder = config.get('last_folder', '.')

    if not bag_name:
        from datetime import datetime
        bag_name = f"rosbag2_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}"

    bag_path = Path(folder) / bag_name

    cmd = ['ros2', 'bag', 'record', '-o', str(bag_path)]

    if topics:
        topic_list = [t.strip() for t in topics.split(',') if t.strip()]
        if topic_list:
            cmd.extend(topic_list)
        else:
            cmd.append('-a')
    else:
        cmd.append('-a')

    if duration:
        cmd.extend(['--duration', str(duration)])

    try:
        RECORDING_PROCESS = subprocess.Popen(cmd)

        if user:
            config['last_user'] = user
            save_config(config)

        return JSONResponse({
            "status": "Recording started",
            "bag_name": bag_name,
            "duration": duration,
            "topics": topics or "all",
            "user": user
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-recording")
async def stop_recording():
    global RECORDING_PROCESS

    if RECORDING_PROCESS is None or RECORDING_PROCESS.poll() is not None:
        raise HTTPException(status_code=400, detail="No recording in progress")

    try:
        RECORDING_PROCESS.terminate()
        RECORDING_PROCESS.wait(timeout=5)
        RECORDING_PROCESS = None
        return JSONResponse({"status": "Recording stopped"})
    except Exception as e:
        RECORDING_PROCESS.kill()
        RECORDING_PROCESS = None
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recording-status")
async def recording_status():
    global RECORDING_PROCESS

    if RECORDING_PROCESS is None:
        return JSONResponse({"recording": False})

    if RECORDING_PROCESS.poll() is None:
        return JSONResponse({"recording": True})
    else:
        RECORDING_PROCESS = None
        return JSONResponse({"recording": False})


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


@app.post("/save-qos")
async def save_qos(
    bag_index: int = Form(...),
    topic: str = Form(...),
    reliability: str = Form(...),
    durability: str = Form(...),
    history: str = Form(...),
    depth: int = Form(...)
):
    metadata = load_metadata()
    bags = metadata.get("bags", [])

    if bag_index >= len(bags):
        raise HTTPException(status_code=404, detail="Bag not found")

    # Initialize qos_settings if not exists
    if 'qos_settings' not in bags[bag_index]:
        bags[bag_index]['qos_settings'] = {}

    # Save QoS settings for the topic
    bags[bag_index]['qos_settings'][topic] = {
        'reliability': reliability,
        'durability': durability,
        'history': history,
        'depth': depth
    }

    metadata['bags'] = bags
    save_metadata(metadata)

    return JSONResponse({
        "status": "QoS settings saved",
        "topic": topic,
        "settings": bags[bag_index]['qos_settings'][topic]
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

