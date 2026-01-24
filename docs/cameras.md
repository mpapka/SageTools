# Camera Guide

This guide covers setting up and capturing images from Sage Continuum cameras.

## Overview

Sage nodes can have multiple cameras attached, including:
- **AXIS** PTZ cameras (pan-tilt-zoom)
- **Hanwha** PTZ cameras
- **Mobotix** thermal cameras

Cameras are accessed via HTTP and typically require SSH tunnels for remote access.

## Network Architecture

```
┌─────────────┐      SSH Tunnel      ┌──────────────┐      HTTP      ┌─────────┐
│ Your Machine│ ──────────────────── │  Sage Node   │ ─────────────  │ Camera  │
│             │     port forwarding  │   (V039)     │   192.168.x.x  │         │
└─────────────┘                      └──────────────┘                └─────────┘
     localhost:8001 ──────────────────────────────────────────────── Camera 1
     localhost:8002 ──────────────────────────────────────────────── Camera 2
```

## Prerequisites

1. **SSH access** to a Sage node (e.g., `V039.sagecontinuum.org`)
2. **SSH key** configured for passwordless login
3. **Camera credentials** (username/password)

## Setting Up SSH Tunnels

### Using the Tunnel Scripts

Start tunnels to a node:

```bash
# Start tunnels to node V039
./scripts/tunnels/startTunnels.sh V039

# List active tunnels
./scripts/tunnels/listTunnels.sh

# Stop all tunnels
./scripts/tunnels/stopTunnels.sh
```

### Manual Tunnel Setup

If you need custom port mappings:

```bash
# Single camera tunnel
ssh -L 8001:192.168.1.101:80 user@V039.sagecontinuum.org -N

# Multiple cameras
ssh -L 8001:192.168.1.101:80 \
    -L 8002:192.168.1.102:80 \
    -L 8003:192.168.1.103:80 \
    user@V039.sagecontinuum.org -N
```

## Camera Configuration

Cameras are configured in `sage/cameras/config.py`:

```python
TUNNEL_MODE = True  # Set to False for direct network access

cameras = {
    "axisPtzApiary": {
        "ip": "192.168.1.101",
        "tunnelPort": 8001,
        "type": "AXIS",
        "model": "AXIS P5655-E",
        "location": "Apiary",
        "username": "root",
        "password": "your_password",
        "capabilities": ["ptz", "visible"],
    },
    # ... more cameras
}
```

### Camera Types and URL Patterns

| Type | Snapshot URL Pattern |
|------|---------------------|
| AXIS | `/axis-cgi/jpg/image.cgi?resolution={res}` |
| Hanwha | `/stw-cgi/image.cgi?msubmenu=jpg&resolution={res}` |
| Mobotix | `/cgi-bin/image.jpg?size={res}` |

### Adding a New Camera

Edit `sage/cameras/config.py`:

```python
cameras["myNewCamera"] = {
    "ip": "192.168.1.200",
    "tunnelPort": 8010,
    "type": "AXIS",  # or "Hanwha", "Mobotix"
    "model": "Camera Model",
    "location": "Location Name",
    "username": "admin",
    "password": "password123",
    "capabilities": ["ptz", "visible"],  # or ["thermal"]
}
```

## Testing Connectivity

### Test All Cameras

```bash
# With tunnels active
sage-camera-test --tunnel

# Direct network access
sage-camera-test
```

**Output**:
```
Testing axisPtzApiary...
  TCP: OK (localhost:8001)
  HTTP: OK (200, 45KB image)

Testing hanwhaPtzApiary...
  TCP: OK (localhost:8002)
  HTTP: OK (200, 52KB image)

Testing mobotixThermal...
  TCP: FAILED (Connection refused)
  HTTP: SKIPPED
```

### Test Specific Camera

```python
from sage.cameras.connection import testCamera
from sage.cameras.config import cameras

result = testCamera(cameras["axisPtzApiary"], useTunnel=True)
print(f"TCP: {result['tcp']}, HTTP: {result['http']}")
```

## Capturing Frames

### Single Frame Capture

```bash
# Capture from all cameras
sage-capture-frame --output=./frames

# List available cameras without capturing
sage-capture-frame --list

# Capture specific camera
sage-capture-frame --camera=axisPtzApiary --output=./frames
```

**Output files**: `frames/axisPtzApiary_20240115_143022.jpg`

### Programmatic Capture

```python
from sage.cameras.captureFrame import captureFrame
from sage.cameras.config import cameras

# Capture single frame
success = captureFrame(
    camera=cameras["axisPtzApiary"],
    outputDir="./frames",
    useTunnel=True
)
```

## Timelapse Capture

### Basic Timelapse

```bash
# Capture for 1 hour at 1 frame per second
sage-timelapse --fps=1 --duration=3600 --output=./timelapse

# Capture for 10 minutes at 0.1 fps (1 frame every 10 seconds)
sage-timelapse --fps=0.1 --duration=600 --output=./timelapse
```

### Simple Mode (No Dashboard)

```bash
sage-timelapse --fps=1 --duration=60 --simple
```

### Dashboard Mode

The default mode shows a live dashboard with:
- Frames captured per camera
- Success/failure rates
- Data transferred
- Estimated completion time

```bash
sage-timelapse --fps=1 --duration=3600

# Dashboard output:
# ┌─────────────────────────────────────────────────────────┐
# │ Camera           │ Frames │ Success │ Failed │ Size    │
# ├──────────────────┼────────┼─────────┼────────┼─────────┤
# │ axisPtzApiary    │    342 │   99.7% │      1 │  15.2MB │
# │ hanwhaPtzApiary  │    341 │   99.4% │      2 │  16.8MB │
# │ mobotixThermal   │    340 │   99.1% │      3 │   8.4MB │
# └─────────────────────────────────────────────────────────┘
# Elapsed: 00:05:42 / 01:00:00   Total: 40.4MB
```

### Timelapse Options

| Option | Description | Default |
|--------|-------------|---------|
| `--fps` | Frames per second | 1 |
| `--duration` | Capture duration in seconds | 60 |
| `--output` | Output directory | `./timelapse` |
| `--simple` | Disable dashboard | False |
| `--cameras` | Comma-separated camera names | All |

## Troubleshooting

### "Connection refused" Error

1. Check SSH tunnel is running: `./scripts/tunnels/listTunnels.sh`
2. Verify tunnel port matches config: `ssh -L 8001:192.168.1.101:80 ...`
3. Check camera is powered on and networked

### "401 Unauthorized" Error

1. Verify credentials in `config.py`
2. Check camera supports digest authentication
3. Try accessing camera directly in browser

### "Timeout" Error

1. Network congestion - try lower FPS for timelapse
2. Camera overloaded - reduce concurrent requests
3. SSH tunnel dropped - restart tunnels

### Image Quality Issues

Adjust resolution in capture:

```python
from sage.cameras.config import getSnapshotUrl

# Get URL with specific resolution
url = getSnapshotUrl(camera, resolution="1920x1080")
```

Available resolutions depend on camera model.

## API Reference

### Key Functions

```python
from sage.cameras.config import (
    cameras,           # Dict of all camera configs
    getHost,          # Get host:port for camera
    getSnapshotUrl,   # Get full snapshot URL
    getAuth,          # Get authentication object
    TUNNEL_MODE,      # Current tunnel mode setting
)

from sage.cameras.connection import (
    testTcpConnection,   # Test TCP connectivity
    testHttpSnapshot,    # Test HTTP image fetch
    testCamera,          # Full connectivity test
)

from sage.cameras.captureFrame import (
    captureFrame,        # Capture single frame
    listCameras,         # List available cameras
)

from sage.cameras.captureTimelapse import (
    CameraStats,         # Statistics tracker
    captureTimelapseFrame,  # Capture one frame
    runTimelapse,        # Full timelapse capture
)
```

## External Resources

- [AXIS Camera API](https://www.axis.com/vapix-library/)
- [Hanwha Camera Documentation](https://www.hanwhasecurity.com/)
- [Mobotix Developer Resources](https://www.mobotix.com/)
