# Testing Guide for ROS2 Bag Manager

## How Recording Works

When you click "Record":
- The Record button turns red and shows "Recording..." with a pulsing dot
- A "Stop Recording" button appears below
- All form fields are disabled during recording
- The recording runs in the background as a ROS2 process

**Recording stops automatically when:**
- You click the "Stop Recording" button
- The duration limit is reached (if you set one)
- You manually stop the ROS2 process

**After recording stops:**
- The bag list automatically refreshes to show the new bag
- Form fields are re-enabled
- You can start a new recording

## Quick Test Commands

### 1. Test Recording with a Simple Topic

Start publishing a test topic in one terminal:
```bash
ros2 topic pub /test_topic std_msgs/msg/String "data: 'Hello ROS2'" -r 10
```

Then in the web interface:
1. Click "⟳ Refresh" in the record section
2. You should see `/test_topic` appear
3. Click it to select it (turns green)
4. Click "Record" button
5. The button will change to "Recording..." with a pulsing red dot
6. A "Stop Recording" button appears below
7. Click "Stop Recording" to stop (or wait if you set a duration)
8. The bag list will automatically refresh when recording stops

### 2. Test with Multiple Topics

Terminal 1 - String topic:
```bash
ros2 topic pub /test_string std_msgs/msg/String "data: 'Test message'" -r 5
```

Terminal 2 - Integer topic:
```bash
ros2 topic pub /test_number std_msgs/msg/Int32 "data: 42" -r 5
```

Terminal 3 - Boolean topic:
```bash
ros2 topic pub /test_bool std_msgs/msg/Bool "data: true" -r 5
```

Then record multiple topics:
1. Refresh topics in the web interface
2. Select `/test_string` and `/test_number` (not `/test_bool`)
3. Set duration to 10 seconds
4. Enter your name
5. Click Record

### 3. Test Recording All Topics

```bash
# Start some publishers
ros2 topic pub /topic1 std_msgs/msg/String "data: 'one'" -r 1 &
ros2 topic pub /topic2 std_msgs/msg/String "data: 'two'" -r 1 &
ros2 topic pub /topic3 std_msgs/msg/String "data: 'three'" -r 1 &
```

Then in web interface:
1. Don't select any topics (leave them all unselected)
2. Set duration to 5 seconds
3. Click Record
4. This will record ALL topics

### 4. Test Playback

After recording a bag:
1. Select the bag from the list
2. Choose playback speed (try 2x or 5x)
3. Enable/disable loop mode
4. Click "Play Bag"

To verify playback is working, open a terminal and echo the topics:
```bash
ros2 topic echo /test_topic
```

### 5. Test Bag Compression

1. Select a bag from the list
2. Click "Compress" button
3. Check your bags folder for the `.7z` file
4. Verify size reduction:
```bash
ls -lh /path/to/your/bags/folder/
```

### 6. Test Rename Feature

1. Select a bag from the list
2. Click the edit icon (✎) next to the bag name
3. Enter a new name in the modal dialog
4. Press OK or Enter
5. The bag should be renamed in the file system and UI

### 7. Test Search and Sort

1. Load multiple bags in a folder
2. Use the search box to filter by name or date
3. Try different sort options:
   - Latest First (default)
   - Oldest First
   - Biggest First
   - Smallest First

## Advanced Testing

### Test with Camera Data (if you have a camera)

```bash
ros2 run usb_cam usb_cam_node_exe
```

Then record the camera topic for a few seconds.

### Test with Simulated Robot

```bash
# Install turtlesim if needed
sudo apt install ros-${ROS_DISTRO}-turtlesim

# Run turtlesim
ros2 run turtlesim turtlesim_node

# Move it around
ros2 run turtlesim turtle_teleop_key
```

Record topics like `/turtle1/cmd_vel` and `/turtle1/pose` while moving the turtle.

### Test Auto-Generated Names

1. Leave the "Bag Name" field empty
2. Click Record
3. A name like `rosbag2_2025_12_12-14_30_45` should be auto-generated

## Verification Checklist

- [ ] Browse button opens folder dialog
- [ ] Bags load automatically after selecting folder
- [ ] Refresh button reloads bags
- [ ] Search filters bags correctly
- [ ] Sort options work
- [ ] Bag selection shows details
- [ ] Rename works
- [ ] Topic refresh discovers running topics
- [ ] Topic chips turn green when selected
- [ ] Recording starts successfully
- [ ] Recording shows nice modal with test command
- [ ] Auto-generated names work
- [ ] Duration limit works
- [ ] User name is saved
- [ ] Playback works
- [ ] Compression works
- [ ] Modals look good and close with Escape/OK
- [ ] Size displays in correct units (B/KB/MB/GB)

## Common Issues

**No topics found when clicking refresh:**
- Make sure ROS2 is sourced: `source /opt/ros/${ROS_DISTRO}/setup.bash`
- Check if any topics exist: `ros2 topic list`

**Recording doesn't start:**
- Check terminal output for errors
- Verify folder permissions
- Make sure ROS2 bag record is installed

**Bags not showing up:**
- Make sure you selected the parent folder containing bag folders
- Bag folders should contain `.mcap` or `.db3` files
- Click the refresh button (⟳)
