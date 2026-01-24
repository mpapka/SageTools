"""
Tests for sage.cameras.captureFrame and captureTimelapse modules.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCaptureFrame:
    """Tests for frame capture functions."""

    def test_captureFrameSuccess(self, tempDir, mockRequests, sampleCameraConfig):
        """Test successful frame capture."""
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.content = b'fake_jpeg_data' * 100
        mockResponse.raise_for_status = MagicMock()
        mockRequests.return_value = mockResponse

        from sage.cameras.captureFrame import captureFrame

        outputDir = Path(tempDir)
        result = captureFrame("testCamera", sampleCameraConfig, outputDir, useTunnel=True)

        assert result is not None
        assert os.path.exists(result)
        assert "testCamera" in result
        assert result.endswith(".jpg")

    def test_captureFrameFailure(self, tempDir, mockRequests, sampleCameraConfig):
        """Test failed frame capture."""
        import requests
        mockRequests.side_effect = requests.exceptions.ConnectionError("Connection failed")

        from sage.cameras.captureFrame import captureFrame

        outputDir = Path(tempDir)
        result = captureFrame("testCamera", sampleCameraConfig, outputDir, useTunnel=True)

        assert result is None

    def test_listCameras(self, capsys):
        """Test listing available cameras."""
        from sage.cameras.captureFrame import listCameras

        listCameras()
        captured = capsys.readouterr()

        assert "Available cameras" in captured.out
        assert "axisPtzApiary" in captured.out


class TestCaptureTimelapse:
    """Tests for timelapse capture functions."""

    def test_cameraStatsInit(self):
        """Test CameraStats initialization."""
        from sage.cameras.captureTimelapse import CameraStats

        stats = CameraStats("testCamera")

        assert stats.name == "testCamera"
        assert stats.captured == 0
        assert stats.failed == 0
        assert stats.totalBytes == 0
        assert stats.lastStatus == "waiting"

    def test_cameraStatsUpdate(self):
        """Test CameraStats tracking."""
        from sage.cameras.captureTimelapse import CameraStats

        stats = CameraStats("testCamera")
        stats.captured = 10
        stats.failed = 2
        stats.totalBytes = 5000
        stats.lastStatus = "ok"

        assert stats.captured == 10
        assert stats.failed == 2
        assert stats.totalBytes == 5000

    def test_formatBytes(self):
        """Test byte formatting."""
        from sage.cameras.captureTimelapse import formatBytes

        assert formatBytes(500) == "500 B"
        assert "KB" in formatBytes(5000)
        assert "MB" in formatBytes(5000000)
        assert "GB" in formatBytes(5000000000)

    def test_formatDuration(self):
        """Test duration formatting."""
        from sage.cameras.captureTimelapse import formatDuration

        assert formatDuration(3661) == "1:01:01"
        assert formatDuration(60) == "0:01:00"
        assert formatDuration(0) == "0:00:00"

    def test_captureTimelapseFrameSuccess(self, tempDir, mockRequests, sampleCameraConfig):
        """Test single timelapse frame capture."""
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.content = b'jpeg_data' * 50
        mockResponse.raise_for_status = MagicMock()
        mockRequests.return_value = mockResponse

        from sage.cameras.captureTimelapse import captureTimelapseFrame, CameraStats

        outputDir = Path(tempDir)
        stats = CameraStats("testCamera")

        success, error, size = captureTimelapseFrame(
            "testCamera", sampleCameraConfig, outputDir, useTunnel=True, stats=stats
        )

        assert success is True
        assert error == ""
        assert size > 0
        assert stats.captured == 1
        assert stats.lastStatus == "ok"

    def test_captureTimelapseFrameFailure(self, tempDir, mockRequests, sampleCameraConfig):
        """Test failed timelapse frame capture."""
        import requests
        mockRequests.side_effect = requests.exceptions.ConnectTimeout()

        from sage.cameras.captureTimelapse import captureTimelapseFrame, CameraStats

        outputDir = Path(tempDir)
        stats = CameraStats("testCamera")

        success, error, size = captureTimelapseFrame(
            "testCamera", sampleCameraConfig, outputDir, useTunnel=True, stats=stats
        )

        assert success is False
        assert "timeout" in error
        assert size == 0
        assert stats.failed == 1
        assert stats.lastStatus == "error"
