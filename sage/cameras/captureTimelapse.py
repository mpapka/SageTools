#!/usr/bin/env python3
"""
Timelapse capture from Sage Continuum cameras.

Provides functions to capture frames at regular intervals with
optional rich dashboard display.
"""

import argparse
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import requests
import urllib3
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import cameras, getSnapshotUrl, getAuth, TUNNEL_MODE

console = Console()
running = True


def signalHandler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    running = False


class CameraStats:
    """Track capture statistics for a camera."""

    def __init__(self, name: str):
        self.name = name
        self.captured = 0
        self.failed = 0
        self.totalBytes = 0
        self.lastStatus = "waiting"
        self.lastError = ""
        self.lastCaptureTime = None


def captureTimelapseFrame(
    cameraName: str,
    camera: dict,
    outputDir: Path,
    useTunnel: bool,
    resolution: str = None,
    stats: CameraStats = None
) -> Tuple[bool, str, int]:
    """
    Capture a single timelapse frame.

    Args:
        cameraName: Name of the camera
        camera: Camera configuration dict
        outputDir: Directory to save the frame
        useTunnel: Whether to use SSH tunnel
        resolution: Optional resolution string
        stats: Optional CameraStats object to update

    Returns:
        Tuple of (success, errorMsg, bytes)
    """
    url = getSnapshotUrl(camera, useTunnel, resolution)
    auth = getAuth(camera)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    filename = f"{cameraName}_{timestamp}.jpg"
    filepath = outputDir / filename

    headers = {
        "User-Agent": "Wget/1.21",
        "Accept": "*/*",
    }

    try:
        response = requests.get(url, auth=auth, headers=headers, timeout=15, verify=False)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        if stats:
            stats.captured += 1
            stats.totalBytes += len(response.content)
            stats.lastStatus = "ok"
            stats.lastError = ""
            stats.lastCaptureTime = datetime.now()

        return True, "", len(response.content)

    except requests.exceptions.ConnectTimeout:
        err = "timeout"
    except requests.exceptions.ConnectionError:
        err = "connection failed"
    except requests.exceptions.HTTPError as e:
        err = f"HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        err = str(e)[:30]

    if stats:
        stats.failed += 1
        stats.lastStatus = "error"
        stats.lastError = err

    return False, err, 0


def formatBytes(b: int) -> str:
    """Format bytes as human readable."""
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"


def formatDuration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))


def createDashboard(
    cameraStats: Dict[str, CameraStats],
    startTime: float,
    frameCount: int,
    interval: float,
    duration: float,
    resolution: str,
    outputDir: Path
) -> Panel:
    """Create the dashboard display panel."""
    elapsed = time.time() - startTime

    # Summary stats
    totalCaptured = sum(s.captured for s in cameraStats.values())
    totalFailed = sum(s.failed for s in cameraStats.values())
    totalBytes = sum(s.totalBytes for s in cameraStats.values())
    successRate = (totalCaptured / (totalCaptured + totalFailed) * 100) if (totalCaptured + totalFailed) > 0 else 0

    # Calculate progress
    if duration > 0:
        progress = min(elapsed / duration * 100, 100)
        remaining = max(duration - elapsed, 0)
    else:
        progress = 0
        remaining = 0

    # Create camera table
    cameraTable = Table(show_header=True, header_style="bold cyan", expand=True)
    cameraTable.add_column("Camera", style="white", width=25)
    cameraTable.add_column("Status", justify="center", width=10)
    cameraTable.add_column("Captured", justify="right", width=10)
    cameraTable.add_column("Failed", justify="right", width=8)
    cameraTable.add_column("Size", justify="right", width=12)
    cameraTable.add_column("Last Error", width=20)

    for name, stats in cameraStats.items():
        if stats.lastStatus == "ok":
            statusText = Text("OK", style="green")
        elif stats.lastStatus == "error":
            statusText = Text("ERROR", style="red")
        else:
            statusText = Text("...", style="yellow")

        cameraTable.add_row(
            name,
            statusText,
            str(stats.captured),
            str(stats.failed) if stats.failed > 0 else "-",
            formatBytes(stats.totalBytes),
            stats.lastError if stats.lastError else "-"
        )

    # Create summary table
    summaryTable = Table(show_header=False, expand=True, box=None)
    summaryTable.add_column("Label", style="bold", width=20)
    summaryTable.add_column("Value", width=20)
    summaryTable.add_column("Label2", style="bold", width=20)
    summaryTable.add_column("Value2", width=20)

    summaryTable.add_row(
        "Elapsed:", formatDuration(elapsed),
        "Remaining:", formatDuration(remaining) if duration > 0 else "infinite"
    )
    summaryTable.add_row(
        "Frames:", f"{frameCount}",
        "Interval:", f"{interval}s ({1/interval:.1f} fps)"
    )
    summaryTable.add_row(
        "Total Captured:", f"{totalCaptured}",
        "Total Failed:", f"{totalFailed}"
    )
    summaryTable.add_row(
        "Success Rate:", f"{successRate:.1f}%",
        "Data Saved:", formatBytes(totalBytes)
    )
    summaryTable.add_row(
        "Resolution:", resolution if resolution else "default",
        "Output:", str(outputDir)
    )

    # Progress bar
    if duration > 0:
        progressBar = f"[{'=' * int(progress / 2)}{' ' * (50 - int(progress / 2))}] {progress:.1f}%"
    else:
        progressBar = "[infinite capture - Ctrl+C to stop]"

    # Combine into layout
    dashboard = Table.grid(expand=True)
    dashboard.add_row(Panel(summaryTable, title="Summary", border_style="blue"))
    dashboard.add_row(Text(progressBar, justify="center", style="bold green"))
    dashboard.add_row(Panel(cameraTable, title="Cameras", border_style="cyan"))

    return Panel(
        dashboard,
        title="[bold white]Timelapse Capture Dashboard[/bold white]",
        subtitle=f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="green"
    )


def runTimelapse(
    cameraNames: List[str] = None,
    interval: float = None,
    fps: float = None,
    duration: float = 0,
    outputDir: str = "./timelapse",
    resolution: str = None,
    useTunnel: bool = None,
    useDashboard: bool = True,
    verbose: bool = False
) -> Dict[str, CameraStats]:
    """
    Run timelapse capture.

    Args:
        cameraNames: List of camera names (None = all)
        interval: Seconds between captures (alternative to fps)
        fps: Frames per second (alternative to interval)
        duration: Total duration in seconds (0 = infinite)
        outputDir: Directory to save frames
        resolution: Optional resolution string
        useTunnel: Whether to use tunnel mode
        useDashboard: Whether to show rich dashboard
        verbose: Whether to show verbose output

    Returns:
        Dictionary of camera statistics
    """
    global running
    running = True

    # Calculate interval from fps or use default
    if fps:
        captureInterval = 1.0 / fps
    elif interval:
        captureInterval = interval
    else:
        captureInterval = 1.0  # Default 1 second

    signal.signal(signal.SIGINT, signalHandler)

    # Determine tunnel mode
    if useTunnel is None:
        useTunnel = TUNNEL_MODE

    # Determine cameras
    if cameraNames:
        selectedCameras = {name: cameras[name] for name in cameraNames if name in cameras}
    else:
        selectedCameras = cameras

    if not selectedCameras:
        console.print("[red]No valid cameras specified[/red]")
        return {}

    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)

    # Initialize stats
    cameraStats = {name: CameraStats(name) for name in selectedCameras}

    modeStr = "tunnel" if useTunnel else "direct"
    fpsVal = 1.0 / captureInterval if captureInterval > 0 else 0

    if useDashboard:
        console.print(f"\n[bold green]Starting timelapse capture...[/bold green]")
        console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")
    else:
        console.print(f"Starting timelapse capture ({modeStr} mode):")
        console.print(f"  Cameras: {', '.join(selectedCameras.keys())}")
        console.print(f"  Interval: {captureInterval}s ({fpsVal:.1f} fps)")
        console.print(f"  Duration: {'infinite' if duration == 0 else f'{duration}s'}")
        if resolution:
            console.print(f"  Resolution: {resolution}")
        console.print(f"  Output: {outputPath}")
        if useTunnel:
            console.print("  Note: Make sure startTunnels.sh is running")
        console.print("\nPress Ctrl+C to stop\n")

    startTime = time.time()
    frameCount = 0

    if useDashboard:
        with Live(console=console, refresh_per_second=2) as live:
            while running:
                if duration > 0 and (time.time() - startTime) >= duration:
                    break

                frameCount += 1

                # Capture from all cameras
                for name, cam in selectedCameras.items():
                    if not running:
                        break
                    captureTimelapseFrame(name, cam, outputPath, useTunnel, resolution, cameraStats[name])

                # Update dashboard
                live.update(createDashboard(
                    cameraStats,
                    startTime,
                    frameCount,
                    captureInterval,
                    duration,
                    resolution,
                    outputPath
                ))

                # Wait for next interval
                nextCapture = startTime + (frameCount * captureInterval)
                sleepTime = nextCapture - time.time()

                while sleepTime > 0 and running:
                    time.sleep(min(sleepTime, 0.5))
                    live.update(createDashboard(
                        cameraStats,
                        startTime,
                        frameCount,
                        captureInterval,
                        duration,
                        resolution,
                        outputPath
                    ))
                    sleepTime = nextCapture - time.time()
    else:
        # Simple mode without dashboard
        while running:
            if duration > 0 and (time.time() - startTime) >= duration:
                break

            frameCount += 1
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            successes = 0
            errors = []
            for name, cam in selectedCameras.items():
                ok, err, _ = captureTimelapseFrame(name, cam, outputPath, useTunnel, resolution, cameraStats[name])
                if ok:
                    successes += 1
                elif err:
                    errors.append(f"{name}: {err}")

            print(f"[{timestamp}] Frame {frameCount}: {successes}/{len(selectedCameras)} captured")
            if verbose and errors:
                for e in errors:
                    print(f"           {e}")

            # Wait for next interval
            nextCapture = startTime + (frameCount * captureInterval)
            sleepTime = nextCapture - time.time()
            if sleepTime > 0 and running:
                time.sleep(sleepTime)

    # Final summary
    elapsed = time.time() - startTime
    totalCaptured = sum(s.captured for s in cameraStats.values())
    totalFailed = sum(s.failed for s in cameraStats.values())
    totalBytes = sum(s.totalBytes for s in cameraStats.values())

    console.print(f"\n[bold green]Capture complete![/bold green]")
    console.print(f"  Duration: {formatDuration(elapsed)}")
    console.print(f"  Frames: {frameCount}")
    console.print(f"  Captured: {totalCaptured}")
    console.print(f"  Failed: {totalFailed}")
    console.print(f"  Data saved: {formatBytes(totalBytes)}")
    console.print(f"  Output: {outputPath}")

    return cameraStats


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Capture timelapse frames")
    parser.add_argument("--camera", "-c", action="append", help="Camera name(s)")
    parser.add_argument("--interval", "-i", type=float, default=None, help="Seconds between captures")
    parser.add_argument("--fps", "-f", type=float, default=None, help="Frames per second")
    parser.add_argument("--duration", "-d", type=float, default=0, help="Total duration (0=infinite)")
    parser.add_argument("--output", "-o", default="./timelapse", help="Output directory")
    parser.add_argument("--resolution", "-r", help="Image resolution")
    parser.add_argument("--tunnel", "-t", action="store_true", help="Force tunnel mode")
    parser.add_argument("--direct", action="store_true", help="Force direct mode")
    parser.add_argument("--simple", "-s", action="store_true", help="Simple output (no dashboard)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Determine tunnel mode
    if args.tunnel:
        useTunnel = True
    elif args.direct:
        useTunnel = False
    else:
        useTunnel = TUNNEL_MODE

    runTimelapse(
        cameraNames=args.camera,
        interval=args.interval,
        fps=args.fps,
        duration=args.duration,
        outputDir=args.output,
        resolution=args.resolution,
        useTunnel=useTunnel,
        useDashboard=not args.simple,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
