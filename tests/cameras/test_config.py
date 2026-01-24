"""
Tests for sage.cameras.config module.
"""

import pytest


class TestCameraConfig:
    """Tests for camera configuration."""

    def test_camerasExist(self):
        """Test that cameras dictionary has entries."""
        from sage.cameras.config import cameras

        assert len(cameras) > 0
        assert 'axisPtzApiary' in cameras
        assert 'hanwhaPtzApiary' in cameras

    def test_cameraHasRequiredFields(self):
        """Test that cameras have required fields."""
        from sage.cameras.config import cameras

        requiredFields = ['ip', 'tunnelPort', 'type', 'username', 'password', 'capabilities']

        for name, cam in cameras.items():
            for field in requiredFields:
                assert field in cam, f"Camera {name} missing field {field}"


class TestGetHost:
    """Tests for getHost function."""

    def test_getHostTunnelMode(self, sampleCameraConfig):
        """Test getHost in tunnel mode."""
        from sage.cameras.config import getHost

        host = getHost(sampleCameraConfig, useTunnel=True)
        assert host == "localhost:8100"

    def test_getHostDirectMode(self, sampleCameraConfig):
        """Test getHost in direct mode."""
        from sage.cameras.config import getHost

        host = getHost(sampleCameraConfig, useTunnel=False)
        assert host == "192.168.1.100"


class TestGetSnapshotUrl:
    """Tests for getSnapshotUrl function."""

    def test_axisSnapshotUrl(self):
        """Test AXIS camera snapshot URL generation."""
        from sage.cameras.config import getSnapshotUrl

        camera = {
            "ip": "192.168.1.1",
            "tunnelPort": 8001,
            "type": "AXIS",
            "username": "user",
            "password": "pass",
        }

        url = getSnapshotUrl(camera, useTunnel=False)
        assert "axis-cgi/jpg/image.cgi" in url
        assert "192.168.1.1" in url

    def test_hanwhaSnapshotUrl(self):
        """Test Hanwha camera snapshot URL generation."""
        from sage.cameras.config import getSnapshotUrl

        camera = {
            "ip": "192.168.1.2",
            "tunnelPort": 8002,
            "type": "Hanwha",
            "username": "user",
            "password": "pass",
        }

        url = getSnapshotUrl(camera, useTunnel=False)
        assert "stw-cgi/video.cgi" in url
        assert "snapshot" in url

    def test_mobotixSnapshotUrl(self):
        """Test Mobotix camera snapshot URL generation."""
        from sage.cameras.config import getSnapshotUrl

        camera = {
            "ip": "192.168.1.3",
            "tunnelPort": 8003,
            "type": "Mobotix",
            "username": "admin",
            "password": "secret",
        }

        url = getSnapshotUrl(camera, useTunnel=False)
        assert "admin:secret@" in url
        assert "record/current.jpg" in url

    def test_snapshotUrlWithResolution(self):
        """Test URL generation with resolution parameter."""
        from sage.cameras.config import getSnapshotUrl

        camera = {
            "ip": "192.168.1.1",
            "tunnelPort": 8001,
            "type": "AXIS",
            "username": "user",
            "password": "pass",
        }

        url = getSnapshotUrl(camera, useTunnel=False, resolution="1280x720")
        assert "resolution=1280x720" in url


class TestGetAuth:
    """Tests for getAuth function."""

    def test_axisAuth(self):
        """Test AXIS camera authentication."""
        from sage.cameras.config import getAuth
        from requests.auth import HTTPDigestAuth

        camera = {"type": "AXIS", "username": "user", "password": "pass"}
        auth = getAuth(camera)

        assert isinstance(auth, HTTPDigestAuth)

    def test_mobotixAuth(self):
        """Test Mobotix camera authentication (embedded in URL)."""
        from sage.cameras.config import getAuth

        camera = {"type": "Mobotix", "username": "admin", "password": "pass"}
        auth = getAuth(camera)

        assert auth is None  # Auth is in URL for Mobotix


class TestFilterFunctions:
    """Tests for camera filtering functions."""

    def test_getCamerasByCapability(self):
        """Test filtering cameras by capability."""
        from sage.cameras.config import getCamerasByCapability

        ptzCameras = getCamerasByCapability("ptz")
        assert len(ptzCameras) > 0
        for name, cam in ptzCameras.items():
            assert "ptz" in cam["capabilities"]

    def test_getCamerasByLocation(self):
        """Test filtering cameras by location."""
        from sage.cameras.config import getCamerasByLocation

        apiaryCameras = getCamerasByLocation("Apiary")
        assert len(apiaryCameras) > 0
        for name, cam in apiaryCameras.items():
            assert cam["location"] == "Apiary"
