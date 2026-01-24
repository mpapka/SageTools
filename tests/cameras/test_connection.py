"""
Tests for sage.cameras.connection module.
"""

import pytest
from unittest.mock import patch, MagicMock
import socket


class TestTcpConnection:
    """Tests for TCP connection testing."""

    def test_tcpConnectionSuccess(self):
        """Test successful TCP connection."""
        with patch('socket.socket') as mockSocket:
            mockInstance = MagicMock()
            mockInstance.connect_ex.return_value = 0
            mockSocket.return_value = mockInstance

            from sage.cameras.connection import testTcpConnection
            success, msg = testTcpConnection("localhost", 8080)

            assert success is True
            assert "open" in msg

    def test_tcpConnectionFailed(self):
        """Test failed TCP connection."""
        with patch('socket.socket') as mockSocket:
            mockInstance = MagicMock()
            mockInstance.connect_ex.return_value = 111  # Connection refused
            mockSocket.return_value = mockInstance

            from sage.cameras.connection import testTcpConnection
            success, msg = testTcpConnection("localhost", 8080)

            assert success is False
            assert "closed" in msg

    def test_tcpConnectionTimeout(self):
        """Test TCP connection timeout."""
        with patch('socket.socket') as mockSocket:
            mockInstance = MagicMock()
            mockInstance.connect_ex.side_effect = socket.timeout()
            mockSocket.return_value = mockInstance

            from sage.cameras.connection import testTcpConnection
            success, msg = testTcpConnection("localhost", 8080)

            assert success is False
            assert "timed out" in msg


class TestHttpSnapshot:
    """Tests for HTTP snapshot testing."""

    def test_httpSnapshotSuccess(self, mockRequests, sampleCameraConfig):
        """Test successful HTTP snapshot."""
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.headers = {'Content-Type': 'image/jpeg'}
        mockResponse.content = b'fake_image_data' * 100  # >1000 bytes
        mockRequests.return_value = mockResponse

        from sage.cameras.connection import testHttpSnapshot
        success, msg, code = testHttpSnapshot(sampleCameraConfig, useTunnel=True)

        assert success is True
        assert code == 200
        assert "OK" in msg

    def test_httpSnapshotFailure(self, mockRequests, sampleCameraConfig):
        """Test failed HTTP snapshot (401 Unauthorized)."""
        mockResponse = MagicMock()
        mockResponse.status_code = 401
        mockResponse.reason = "Unauthorized"
        mockRequests.return_value = mockResponse

        from sage.cameras.connection import testHttpSnapshot
        success, msg, code = testHttpSnapshot(sampleCameraConfig, useTunnel=True)

        assert success is False
        assert code == 401

    def test_httpSnapshotTimeout(self, mockRequests, sampleCameraConfig):
        """Test HTTP snapshot timeout."""
        import requests
        mockRequests.side_effect = requests.exceptions.ConnectTimeout()

        from sage.cameras.connection import testHttpSnapshot
        success, msg, code = testHttpSnapshot(sampleCameraConfig, useTunnel=True)

        assert success is False
        assert "timed out" in msg


class TestCameraTest:
    """Tests for full camera testing."""

    def test_testCameraSuccess(self, mockRequests):
        """Test full camera test with success."""
        from sage.cameras.config import cameras
        from sage.cameras.connection import testCamera

        # Mock both TCP and HTTP success
        with patch('sage.cameras.connection.testTcpConnection') as mockTcp:
            mockTcp.return_value = (True, "port open")

            mockResponse = MagicMock()
            mockResponse.status_code = 200
            mockResponse.headers = {'Content-Type': 'image/jpeg'}
            mockResponse.content = b'x' * 2000
            mockRequests.return_value = mockResponse

            # Test a real camera from config
            camName = list(cameras.keys())[0]
            result = testCamera(camName, cameras[camName], useTunnel=True)

            assert result is True

    def test_testCameraNoConnectivity(self):
        """Test camera test with no connectivity."""
        from sage.cameras.config import cameras
        from sage.cameras.connection import testCamera

        with patch('sage.cameras.connection.testTcpConnection') as mockTcp:
            mockTcp.return_value = (False, "connection refused")

            camName = list(cameras.keys())[0]
            result = testCamera(camName, cameras[camName], useTunnel=True)

            assert result is False
