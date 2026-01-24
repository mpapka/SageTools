#!/usr/bin/env python3
"""
Single frame capture from Sage Continuum cameras.

Provides functions to capture individual snapshots from cameras.
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import cameras, getSnapshotUrl, getAuth, TUNNEL_MODE


def captureFrame(
    cameraName: str,
    camera: dict,
    outputDir: Path,
    useTunnel: bool,
    resolution: str = None
) -> Optional[str]:
    """
    Capture a single frame from the specified camera.

    Args:
        cameraName: Name of the camera
        camera: Camera configuration dict
        outputDir: Directory to save the frame
        useTunnel: Whether to use SSH tunnel
        resolution: Optional resolution string

    Returns:
        Path to saved file, or None on error
    """
    url = getSnapshotUrl(camera, useTunnel, resolution)
    auth = getAuth(camera)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{cameraName}_{timestamp}.jpg"
    filepath = outputDir / filename

    headers = {
        "User-Agent": "Wget/1.21",
        "Accept": "*/*",
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=10, verify=False)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"[OK] {cameraName}: saved to {filepath} ({len(response.content)} bytes)")
        return str(filepath)

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {cameraName}: {e}")
        return None


def listCameras():
    """Print available cameras."""
    print("\nAvailable cameras:")
    print("-" * 70)
    for name, cam in cameras.items():
        caps = ", ".join(cam["capabilities"])
        print(f"  {name:25} | {cam['ip']:15} | {cam['location']:8} | {caps}")
    print()


def captureFromAll(
    outputDir: str = "./frames",
    resolution: str = None,
    useTunnel: bool = None,
    cameraNames: list = None
) -> dict:
    """
    Capture frames from multiple cameras.

    Args:
        outputDir: Directory to save frames
        resolution: Optional resolution string
        useTunnel: Whether to use tunnel mode (None = use config default)
        cameraNames: List of camera names to capture from (None = all)

    Returns:
        Dictionary of {camera_name: filepath or None}
    """
    if useTunnel is None:
        useTunnel = TUNNEL_MODE

    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)

    # Determine which cameras to capture from
    if cameraNames:
        captureCameras = {n: cameras[n] for n in cameraNames if n in cameras}
        for name in cameraNames:
            if name not in cameras:
                print(f"Unknown camera: {name}")
    else:
        captureCameras = cameras

    modeStr = "tunnel" if useTunnel else "direct"
    resStr = f", resolution: {resolution}" if resolution else ""
    print(f"Capturing frames from {len(captureCameras)} camera(s) ({modeStr} mode{resStr})...")
    if useTunnel:
        print("Make sure startTunnels.sh is running.")
    print()

    results = {}
    for name, cam in captureCameras.items():
        results[name] = captureFrame(name, cam, outputPath, useTunnel, resolution)

    return results


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Capture frames from cameras")
    parser.add_argument("cameras", nargs="*", help="Camera names (empty = all)")
    parser.add_argument("--list", "-l", action="store_true", help="List cameras")
    parser.add_argument("--output", "-o", default="./frames", help="Output directory")
    parser.add_argument("--resolution", "-r", help="Image resolution (e.g., 1920x1080, 1280x720, 640x480)")
    parser.add_argument("--tunnel", "-t", action="store_true", help="Force tunnel mode")
    parser.add_argument("--direct", "-d", action="store_true", help="Force direct mode")
    args = parser.parse_args()

    if args.list:
        listCameras()
        return

    # Determine tunnel mode
    if args.tunnel:
        useTunnel = True
    elif args.direct:
        useTunnel = False
    else:
        useTunnel = TUNNEL_MODE

    captureFromAll(
        outputDir=args.output,
        resolution=args.resolution,
        useTunnel=useTunnel,
        cameraNames=args.cameras if args.cameras else None
    )


if __name__ == "__main__":
    main()
