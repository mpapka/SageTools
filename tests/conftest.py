"""
Shared pytest fixtures for Sage tools tests.
"""

import pytest
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Create a mock sage_data_client module if it's not installed
# This allows tests to run without the actual dependency
if 'sage_data_client' not in sys.modules:
    mockSageModule = MagicMock()
    mockSageModule.query = MagicMock(return_value=pd.DataFrame())
    sys.modules['sage_data_client'] = mockSageModule


@pytest.fixture
def tempDir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sampleTemperatureDf():
    """Create a sample temperature DataFrame."""
    now = datetime.now()
    timestamps = [now - timedelta(hours=i) for i in range(100)]
    return pd.DataFrame({
        'timestamp': timestamps,
        'value': [20 + (i % 10) for i in range(100)],  # 20-29 C
        'name': ['env.temperature'] * 100,
        'meta.vsn': ['W01B'] * 100,
        'meta.sensor': ['bme280'] * 100,
        'meta.host': ['rpi.host'] * 100,
    })


@pytest.fixture
def sampleNodeRegistryDf():
    """Create a sample node registry DataFrame."""
    now = datetime.now()
    return pd.DataFrame({
        'vsn': ['W01B', 'W01C', 'W08D', 'H001', 'V002'],
        'lat': [41.87, 41.88, 41.89, 42.0, None],
        'lon': [-87.62, -87.63, -87.64, -88.0, None],
        'firstSeen': [now - timedelta(days=365*i) for i in range(1, 6)],
        'lastSeen': [now - timedelta(days=i) for i in range(5)],
        'activePeriods': ['[]'] * 5,
    })


@pytest.fixture
def sampleUptimeDf():
    """Create a sample sys.uptime DataFrame."""
    now = datetime.now()
    timestamps = [now - timedelta(hours=i) for i in range(10)]
    return pd.DataFrame({
        'timestamp': timestamps,
        'value': [i * 3600 for i in range(10)],  # Uptime in seconds
        'name': ['sys.uptime'] * 10,
        'meta.vsn': ['W01B'] * 5 + ['W01C'] * 5,
    })


@pytest.fixture
def mockSageDataClient():
    """Mock sage_data_client.query."""
    with patch('sage_data_client.query') as mock:
        yield mock


@pytest.fixture
def mockRequests():
    """Mock requests.get for camera tests."""
    with patch('requests.get') as mock:
        yield mock


@pytest.fixture
def sampleCameraConfig():
    """Sample camera configuration for testing."""
    return {
        "ip": "192.168.1.100",
        "tunnelPort": 8100,
        "type": "AXIS",
        "model": "Test Camera",
        "location": "Test",
        "username": "testuser",
        "password": "testpass",
        "capabilities": ["ptz", "thermal"],
    }


@pytest.fixture
def sampleCsvFile(tempDir, sampleTemperatureDf):
    """Create a sample CSV file for testing."""
    filepath = os.path.join(tempDir, "test_data.csv")
    sampleTemperatureDf.to_csv(filepath, index=False)
    return filepath


@pytest.fixture
def sampleNodeRegistryCsv(tempDir, sampleNodeRegistryDf):
    """Create a sample node registry CSV file."""
    filepath = os.path.join(tempDir, "nodeRegistry.csv")
    sampleNodeRegistryDf.to_csv(filepath, index=False)
    return filepath


@pytest.fixture
def malformedCsvFile(tempDir):
    """Create a CSV file with inconsistent columns."""
    filepath = os.path.join(tempDir, "malformed.csv")
    with open(filepath, 'w') as f:
        f.write("timestamp,value,meta.vsn\n")
        f.write("2024-01-01T00:00:00Z,25.0,W01B\n")
        f.write("2024-01-01T01:00:00Z,26.0,W01B,extra_value\n")  # Extra column
        f.write("2024-01-01T02:00:00Z,27.0\n")  # Missing column
    return filepath


@pytest.fixture
def regionsJsonFile(tempDir):
    """Create a sample regions.json file."""
    import json
    filepath = os.path.join(tempDir, "regions.json")
    with open(filepath, 'w') as f:
        json.dump({
            "usa": {"lat": [24.0, 49.0], "lon": [-125.0, -66.0]},
            "chicago": {"lat": [41.6, 42.1], "lon": [-88.0, -87.5]}
        }, f)
    return filepath
