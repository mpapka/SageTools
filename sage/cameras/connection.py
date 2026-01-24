#!/usr/bin/env python3
"""
Camera connectivity testing.

Provides functions to test TCP and HTTP connectivity to cameras,
verifying that tunnels are working and cameras are accessible.
"""

import argparse
import socket
import sys
from typing import Tuple, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import cameras, getSnapshotUrl, getAuth, getHost, TUNNEL_MODE


def testTcpConnection(host: str, port: int, timeout: float = 5) -> Tuple[bool, str]:
    """
    Test if we can establish a TCP connection.

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (success, message)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return True, "port open"
        else:
            return False, f"port closed (error {result})"
    except socket.timeout:
        return False, "connection timed out"
    except socket.error as e:
        return False, str(e)


def testHttpSnapshot(camera: dict, useTunnel: bool, timeout: float = 10) -> Tuple[bool, str, int]:
    """
    Test if we can fetch a snapshot from the camera.

    Args:
        camera: Camera configuration dict
        useTunnel: Whether to use SSH tunnel
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, message, HTTP status code)
    """
    url = getSnapshotUrl(camera, useTunnel)
    auth = getAuth(camera)

    headers = {
        "User-Agent": "Wget/1.21",
        "Accept": "*/*",
        "Connection": "Keep-Alive",
    }

    try:
        response = requests.get(
            url,
            auth=auth,
            headers=headers,
            timeout=timeout,
            verify=False
        )
        contentType = response.headers.get("Content-Type", "")
        contentLength = len(response.content)

        if response.status_code == 200:
            if "image" in contentType or contentLength > 1000:
                return True, f"OK ({contentLength} bytes)", response.status_code
            else:
                return False, f"unexpected content: {contentType}", response.status_code
        else:
            return False, response.reason, response.status_code

    except requests.exceptions.ConnectTimeout:
        return False, "connection timed out", 0
    except requests.exceptions.ConnectionError as e:
        errStr = str(e)
        if "RemoteDisconnected" in errStr:
            return False, "server closed connection", 0
        if "Connection refused" in errStr:
            return False, "connection refused (tunnel not running?)", 0
        return False, "connection failed", 0
    except requests.exceptions.ReadTimeout:
        return False, "read timed out", 0
    except requests.exceptions.SSLError:
        return False, "SSL error", 0
    except requests.exceptions.RequestException as e:
        return False, str(e), 0


def testCamera(name: str, camera: dict, useTunnel: bool) -> bool:
    """
    Run all tests for a single camera.

    Args:
        name: Camera name
        camera: Camera configuration dict
        useTunnel: Whether to use SSH tunnel

    Returns:
        True if camera is accessible
    """
    hostStr = getHost(camera, useTunnel)

    if useTunnel:
        host = "localhost"
        port = camera["tunnelPort"]
    else:
        host = camera["ip"]
        port = 80

    print(f"\n{name}")
    print(f"  Target: {hostStr}")
    print("-" * 50)

    # Test 1: TCP connection
    tcpOk, tcpMsg = testTcpConnection(host, port)
    status = "OK" if tcpOk else "FAIL"
    print(f"  TCP connection: [{status}] {tcpMsg}")

    if not tcpOk:
        print(f"  HTTP snapshot:  [SKIP] no connectivity")
        if useTunnel:
            print(f"  Hint: Is startTunnels.sh running?")
        return False

    # Test 2: HTTP snapshot
    httpOk, httpMsg, httpCode = testHttpSnapshot(camera, useTunnel)
    status = "OK" if httpOk else "FAIL"
    codeStr = f" (HTTP {httpCode})" if httpCode else ""
    print(f"  HTTP snapshot:  [{status}] {httpMsg}{codeStr}")

    return httpOk


def testAllCameras(cameraNames: list = None, useTunnel: bool = None) -> dict:
    """
    Test connectivity to multiple cameras.

    Args:
        cameraNames: List of camera names to test (None = all)
        useTunnel: Whether to use tunnel mode (None = use config default)

    Returns:
        Dictionary of {camera_name: success}
    """
    if useTunnel is None:
        useTunnel = TUNNEL_MODE

    if cameraNames:
        testCameras = {n: cameras[n] for n in cameraNames if n in cameras}
        invalid = [n for n in cameraNames if n not in cameras]
        for n in invalid:
            print(f"Unknown camera: {n}")
    else:
        testCameras = cameras

    if not testCameras:
        print("No cameras to test")
        return {}

    modeStr = "tunnel" if useTunnel else "direct"
    print(f"Testing camera connectivity ({modeStr} mode)...")

    if useTunnel:
        print("Make sure startTunnels.sh is running in another terminal.")

    results = {}
    for name, cam in testCameras.items():
        results[name] = testCamera(name, cam, useTunnel)

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} cameras accessible")

    if passed == 0:
        if useTunnel:
            print("\nNo cameras reachable. Check:")
            print("  - startTunnels.sh is running")
            print("  - SSH key path is correct")
            print("  - Node name is correct (e.g., V039)")
        else:
            print("\nNo cameras reachable via direct connection.")
            print("Try tunnel mode: python -m sage.cameras.connection --tunnel")
    elif passed < total:
        print("\nSome cameras unreachable:")
        for name, ok in results.items():
            if not ok:
                print(f"  - {name}")

    return results


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Test camera connectivity")
    parser.add_argument("cameras", nargs="*", help="Camera names (empty = all)")
    parser.add_argument("--tunnel", "-t", action="store_true", help="Force tunnel mode")
    parser.add_argument("--direct", "-d", action="store_true", help="Force direct mode")
    args = parser.parse_args()

    # Determine tunnel mode
    if args.tunnel:
        useTunnel = True
    elif args.direct:
        useTunnel = False
    else:
        useTunnel = TUNNEL_MODE

    results = testAllCameras(args.cameras if args.cameras else None, useTunnel)

    # Return appropriate exit code
    if not results or all(not v for v in results.values()):
        sys.exit(1)
    elif any(not v for v in results.values()):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
