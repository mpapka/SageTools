"""
Tests for sage.beehive.discovery module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestListMetrics:
    """Tests for listMetrics function."""

    def test_listMetricsFindsSensors(self, mockSageDataClient):
        """Test that listMetrics returns available metrics."""
        # Setup mock response
        mockSageDataClient.return_value = pd.DataFrame({
            'name': ['env.temperature', 'env.humidity', 'sys.uptime', 'env.temperature'],
            'value': [25.0, 60.0, 3600, 26.0],
        })

        from sage.beehive.discovery.listMetrics import listMetrics
        result = listMetrics("W01B", "-5m")

        assert result is not None
        assert 'env.temperature' in result
        assert 'env.humidity' in result
        assert 'sys.uptime' in result
        assert len(result) == 3  # Unique metrics

    def test_listMetricsNoData(self, mockSageDataClient):
        """Test listMetrics with no data returned."""
        mockSageDataClient.return_value = pd.DataFrame()

        from sage.beehive.discovery.listMetrics import listMetrics
        result = listMetrics("INVALID", "-5m")

        assert result is None


class TestNodeLife:
    """Tests for nodeLife functions."""

    def test_findNodeLifeSuccess(self, mockSageDataClient):
        """Test findNodeLife with valid node."""
        now = datetime.now()
        firstTime = now - timedelta(days=365)

        # Mock for last record
        mockSageDataClient.side_effect = [
            pd.DataFrame({'timestamp': [now], 'value': [3600]}),  # Last record
            pd.DataFrame({'timestamp': [firstTime], 'value': [0]}),  # First record
        ]

        from sage.beehive.discovery.nodeLife import findNodeLife
        result = findNodeLife("W01B")

        assert result is not None
        firstSeen, lastSeen = result
        assert firstSeen == firstTime
        assert lastSeen == now

    def test_findNodeLifeNotFound(self, mockSageDataClient):
        """Test findNodeLife with invalid node."""
        mockSageDataClient.return_value = pd.DataFrame()

        from sage.beehive.discovery.nodeLife import findNodeLife
        result = findNodeLife("INVALID")

        assert result is None


class TestListNodes:
    """Tests for listNodes checkpoint functions."""

    def test_saveAndLoadCheckpoint(self, tempDir):
        """Test checkpoint save/load cycle."""
        import os
        checkpointFile = os.path.join(tempDir, ".test.checkpoint")

        from sage.beehive.discovery.listNodes import saveCheckpoint, loadCheckpoint

        nodes = pd.DataFrame({'vsn': ['W01B', 'W01C']})
        activityData = {'W01B': [('2024-01-01', '2024-01-07')]}
        currentStart = datetime(2024, 1, 7)

        saveCheckpoint(nodes, activityData, currentStart, checkpointFile)

        checkpoint = loadCheckpoint(checkpointFile)
        assert checkpoint is not None
        assert 'nodes' in checkpoint
        assert 'activityData' in checkpoint
        assert 'currentStart' in checkpoint

    def test_loadCheckpointNotExists(self, tempDir):
        """Test loading non-existent checkpoint."""
        import os
        checkpointFile = os.path.join(tempDir, ".nonexistent.checkpoint")

        from sage.beehive.discovery.listNodes import loadCheckpoint
        result = loadCheckpoint(checkpointFile)

        assert result is None
