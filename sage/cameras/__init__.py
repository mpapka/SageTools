"""
Camera tools for Sage Continuum cameras.

Modules:
    config: Camera configuration and URL generation
    connection: Connection testing
    captureFrame: Single frame capture
    captureTimelapse: Timelapse capture with optional dashboard
"""

from .config import cameras, getHost, getSnapshotUrl, getAuth, TUNNEL_MODE
from .connection import testCamera, testTcpConnection, testHttpSnapshot
from .captureFrame import captureFrame, listCameras
from .captureTimelapse import runTimelapse, CameraStats
