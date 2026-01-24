"""
Camera configuration for Sage Continuum cameras.

Provides camera definitions and URL generation for different camera types
(AXIS, Hanwha, Mobotix). Supports both direct connections and SSH tunnel mode.
"""

from typing import Optional
from requests.auth import HTTPDigestAuth, HTTPBasicAuth

# Global tunnel mode setting - set to True when using SSH tunnels via startTunnels.sh
TUNNEL_MODE = True

# Camera definitions
cameras = {
    # PTZ Cameras
    "axisPtzApiary": {
        "ip": "130.202.23.91",
        "tunnelPort": 8091,
        "type": "AXIS",
        "model": "Q6055-E PTZ",
        "location": "Apiary",
        "username": "camera",
        "password": "0Bscura#",
        "capabilities": ["ptz"],
    },
    "hanwhaPtzApiary": {
        "ip": "130.202.23.92",
        "tunnelPort": 8092,
        "type": "Hanwha",
        "model": "XNP-6400RW",
        "location": "Apiary",
        "username": "camera",
        "password": "0Bscura#",
        "capabilities": ["ptz"],
    },
    "hanwhaPtzAtmos": {
        "ip": "130.202.23.153",
        "tunnelPort": 8153,
        "type": "Hanwha",
        "model": "XNP-6400RW",
        "location": "ATMOS",
        "username": "camera",
        "password": "0Bscura#",
        "capabilities": ["ptz"],
    },
    # Thermal Camera
    "mobotixThermalApiary": {
        "ip": "130.202.23.119",
        "tunnelPort": 8119,
        "type": "Mobotix",
        "model": "M16",
        "location": "Apiary",
        "username": "admin",
        "password": "wagglesage",
        "capabilities": ["thermal", "pt"],
    },
    # Static Sky-Facing Cameras
    "hanwhaSkyApiary1": {
        "ip": "130.202.23.149",
        "tunnelPort": 8149,
        "type": "Hanwha",
        "model": "XNV-8081Z",
        "location": "Apiary",
        "username": "camera",
        "password": "0Bscura#",
        "capabilities": ["static", "sky"],
    },
    "hanwhaSkyApiary2": {
        "ip": "130.202.23.150",
        "tunnelPort": 8150,
        "type": "Hanwha",
        "model": "XNV-8081Z",
        "location": "Apiary",
        "username": "camera",
        "password": "0Bscura#",
        "capabilities": ["static", "sky"],
    },
}


def getHost(camera: dict, useTunnel: bool = None) -> str:
    """
    Get the host:port to connect to based on tunnel mode.

    Args:
        camera: Camera configuration dict
        useTunnel: Whether to use SSH tunnel (None = use TUNNEL_MODE)

    Returns:
        Host string (e.g., "localhost:8091" or "130.202.23.91")
    """
    if useTunnel is None:
        useTunnel = TUNNEL_MODE

    if useTunnel:
        return f"localhost:{camera['tunnelPort']}"
    else:
        return camera["ip"]


def getSnapshotUrl(camera: dict, useTunnel: bool = None, resolution: str = None) -> str:
    """
    Generate the snapshot URL for a given camera configuration.

    Args:
        camera: Camera configuration dict
        useTunnel: Whether to use SSH tunnel (None = use TUNNEL_MODE)
        resolution: Optional resolution string like "1920x1080", "1280x720", "640x480"

    Returns:
        Full URL for capturing a snapshot
    """
    host = getHost(camera, useTunnel)
    camType = camera["type"]

    if camType == "AXIS":
        url = f"http://{host}/axis-cgi/jpg/image.cgi"
        if resolution:
            url += f"?resolution={resolution}"
        return url
    elif camType == "Hanwha":
        url = f"http://{host}/stw-cgi/video.cgi?msubmenu=snapshot&action=view"
        if resolution:
            url += f"&resolution={resolution}"
        return url
    elif camType == "Mobotix":
        username = camera["username"]
        password = camera["password"]
        url = f"http://{username}:{password}@{host}/record/current.jpg"
        if resolution:
            url += f"?size={resolution}"
        return url
    else:
        raise ValueError(f"Unknown camera type: {camType}")


def getAuth(camera: dict) -> Optional[HTTPDigestAuth]:
    """
    Get authentication object for camera.

    Args:
        camera: Camera configuration dict

    Returns:
        Authentication object (HTTPDigestAuth, HTTPBasicAuth, or None)
    """
    camType = camera["type"]
    username = camera["username"]
    password = camera["password"]

    if camType == "Mobotix":
        return None  # Auth embedded in URL
    elif camType == "Hanwha":
        return HTTPDigestAuth(username, password)
    elif camType == "AXIS":
        return HTTPDigestAuth(username, password)  # AXIS also uses digest
    else:
        return HTTPBasicAuth(username, password)


def listCameras() -> dict:
    """
    Get all available cameras.

    Returns:
        Dictionary of camera configurations
    """
    return cameras


def getCamerasByCapability(capability: str) -> dict:
    """
    Filter cameras by capability.

    Args:
        capability: Capability to filter by (e.g., "ptz", "thermal", "sky")

    Returns:
        Dictionary of matching cameras
    """
    return {
        name: cam for name, cam in cameras.items()
        if capability in cam.get("capabilities", [])
    }


def getCamerasByLocation(location: str) -> dict:
    """
    Filter cameras by location.

    Args:
        location: Location to filter by (e.g., "Apiary", "ATMOS")

    Returns:
        Dictionary of matching cameras
    """
    return {
        name: cam for name, cam in cameras.items()
        if cam.get("location", "").lower() == location.lower()
    }
