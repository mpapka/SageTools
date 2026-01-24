# Camera API

Module: `sage.cameras`

## config

Camera configuration and URL generation.

### Constants

#### `TUNNEL_MODE: bool`

Global flag for SSH tunnel mode. Default: `True`

When `True`, cameras are accessed via localhost tunnel ports.
When `False`, cameras are accessed directly by IP.

#### `cameras: dict`

Dictionary of all configured cameras.

**Structure**:
```python
cameras = {
    "cameraName": {
        "ip": "192.168.1.100",       # Direct IP address
        "tunnelPort": 8001,          # Localhost port when tunneled
        "type": "AXIS",              # AXIS, Hanwha, or Mobotix
        "model": "AXIS P5655-E",     # Camera model
        "location": "Apiary",        # Physical location
        "username": "root",          # HTTP auth username
        "password": "password",      # HTTP auth password
        "capabilities": ["ptz", "visible"],  # Feature list
    },
    # ... more cameras
}
```

### Functions

#### `getHost(camera: dict, useTunnel: bool = None) -> str`

Get the host:port string for a camera.

**Parameters**:
- `camera` (dict): Camera configuration
- `useTunnel` (bool, optional): Override TUNNEL_MODE

**Returns**:
- `str`: Host string (e.g., "localhost:8001" or "192.168.1.100")

**Example**:
```python
from sage.cameras.config import cameras, getHost

host = getHost(cameras["axisPtzApiary"], useTunnel=True)
# Returns: "localhost:8001"
```

#### `getSnapshotUrl(camera: dict, useTunnel: bool = None, resolution: str = None) -> str`

Get the full snapshot URL for a camera.

**Parameters**:
- `camera` (dict): Camera configuration
- `useTunnel` (bool, optional): Override TUNNEL_MODE
- `resolution` (str, optional): Image resolution (e.g., "1920x1080")

**Returns**:
- `str`: Full URL for snapshot capture

**Example**:
```python
from sage.cameras.config import cameras, getSnapshotUrl

url = getSnapshotUrl(cameras["axisPtzApiary"], resolution="1280x720")
# Returns: "http://localhost:8001/axis-cgi/jpg/image.cgi?resolution=1280x720"
```

#### `getAuth(camera: dict) -> HTTPDigestAuth | None`

Get authentication object for a camera.

**Parameters**:
- `camera` (dict): Camera configuration

**Returns**:
- `HTTPDigestAuth`: Authentication object for requests
- `None`: If no credentials configured

**Example**:
```python
import requests
from sage.cameras.config import cameras, getSnapshotUrl, getAuth

url = getSnapshotUrl(cameras["axisPtzApiary"])
auth = getAuth(cameras["axisPtzApiary"])
response = requests.get(url, auth=auth, timeout=10)
```

#### `getCamerasByCapability(capability: str) -> dict`

Filter cameras by capability.

**Parameters**:
- `capability` (str): Capability to filter by (e.g., "ptz", "thermal")

**Returns**:
- `dict`: Filtered cameras dictionary

#### `getCamerasByLocation(location: str) -> dict`

Filter cameras by location.

**Parameters**:
- `location` (str): Location to filter by

**Returns**:
- `dict`: Filtered cameras dictionary

---

## connection

Connectivity testing utilities.

### Functions

#### `testTcpConnection(host: str, port: int, timeout: float = 5.0) -> bool`

Test TCP connectivity to a host:port.

**Parameters**:
- `host` (str): Hostname or IP
- `port` (int): Port number
- `timeout` (float): Connection timeout. Default: 5.0

**Returns**:
- `bool`: True if connection successful

**Example**:
```python
from sage.cameras.connection import testTcpConnection

if testTcpConnection("localhost", 8001):
    print("Tunnel is active")
```

#### `testHttpSnapshot(camera: dict, useTunnel: bool = None, timeout: float = 10.0) -> dict`

Test HTTP snapshot retrieval.

**Parameters**:
- `camera` (dict): Camera configuration
- `useTunnel` (bool, optional): Override TUNNEL_MODE
- `timeout` (float): Request timeout. Default: 10.0

**Returns**:
- `dict`:
  - `success` (bool): True if image retrieved
  - `statusCode` (int): HTTP status code
  - `size` (int): Image size in bytes
  - `error` (str): Error message if failed

#### `testCamera(camera: dict, useTunnel: bool = None) -> dict`

Run full connectivity test on a camera.

**Parameters**:
- `camera` (dict): Camera configuration
- `useTunnel` (bool, optional): Override TUNNEL_MODE

**Returns**:
- `dict`:
  - `tcp` (bool): TCP connectivity result
  - `http` (dict): HTTP test results
  - `name` (str): Camera name

### CLI Usage

```bash
sage-camera-test [--tunnel] [--camera=name]
```

---

## captureFrame

Single frame capture.

### Functions

#### `captureFrame(camera: dict, outputDir: str, useTunnel: bool = None, timestamp: bool = True) -> str | None`

Capture a single frame from a camera.

**Parameters**:
- `camera` (dict): Camera configuration
- `outputDir` (str): Output directory path
- `useTunnel` (bool, optional): Override TUNNEL_MODE
- `timestamp` (bool): Include timestamp in filename. Default: True

**Returns**:
- `str`: Path to saved image file
- `None`: If capture failed

**Example**:
```python
from sage.cameras.config import cameras
from sage.cameras.captureFrame import captureFrame

filepath = captureFrame(
    cameras["axisPtzApiary"],
    outputDir="./frames",
    useTunnel=True
)
print(f"Saved: {filepath}")
# Output: Saved: ./frames/axisPtzApiary_20240115_143022.jpg
```

#### `listCameras() -> list[str]`

Get list of configured camera names.

**Returns**:
- `list[str]`: Camera names

### CLI Usage

```bash
# Capture from all cameras
sage-capture-frame --output=./frames

# List cameras
sage-capture-frame --list

# Capture specific camera
sage-capture-frame --camera=axisPtzApiary --output=./frames
```

---

## captureTimelapse

Timelapse capture with optional dashboard.

### Classes

#### `CameraStats`

Track capture statistics for a camera.

**Attributes**:
- `name` (str): Camera name
- `framesCaptures` (int): Successful captures
- `framesFailed` (int): Failed captures
- `totalBytes` (int): Total data transferred
- `lastCaptureTime` (float): Timestamp of last capture

**Methods**:
- `update(success: bool, size: int)`: Update stats after capture
- `successRate() -> float`: Calculate success percentage

### Functions

#### `captureTimelapseFrame(camera: dict, outputDir: str, frameNum: int, useTunnel: bool = None) -> tuple[bool, int]`

Capture a single timelapse frame.

**Parameters**:
- `camera` (dict): Camera configuration
- `outputDir` (str): Output directory
- `frameNum` (int): Frame sequence number
- `useTunnel` (bool, optional): Override TUNNEL_MODE

**Returns**:
- `tuple[bool, int]`: (success, file_size_bytes)

#### `runTimelapse(fps: float, duration: int, outputDir: str, simple: bool = False, cameras: list[str] = None)`

Run a full timelapse capture session.

**Parameters**:
- `fps` (float): Frames per second
- `duration` (int): Duration in seconds
- `outputDir` (str): Output directory
- `simple` (bool): Disable dashboard. Default: False
- `cameras` (list[str], optional): Camera names to capture. Default: all

**Example**:
```python
from sage.cameras.captureTimelapse import runTimelapse

# 1 hour timelapse at 1 fps
runTimelapse(
    fps=1,
    duration=3600,
    outputDir="./timelapse",
    simple=False
)
```

#### `formatBytes(size: int) -> str`

Format byte count as human-readable string.

#### `formatDuration(seconds: float) -> str`

Format seconds as HH:MM:SS.

### CLI Usage

```bash
sage-timelapse \
    --fps=1 \
    --duration=3600 \
    --output=./timelapse \
    [--simple] \
    [--cameras=axisPtzApiary,hanwhaPtzApiary]
```
