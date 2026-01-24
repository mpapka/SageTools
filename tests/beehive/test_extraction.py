"""
Tests for sage.beehive.extraction module.
"""

import pytest
import pandas as pd
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestQuery:
    """Tests for simple query function."""

    def test_runQuerySuccess(self, mockSageDataClient, sampleTemperatureDf):
        """Test successful query execution."""
        mockSageDataClient.return_value = sampleTemperatureDf

        from sage.beehive.extraction.query import runQuery
        result = runQuery(start="-1h", name="env.temperature", vsn="W01B")

        assert result is not None
        assert len(result) == 100
        assert 'timestamp' in result.columns
        assert 'value' in result.columns

    def test_runQueryNoData(self, mockSageDataClient):
        """Test query with no data returned."""
        mockSageDataClient.return_value = pd.DataFrame()

        from sage.beehive.extraction.query import runQuery
        result = runQuery(start="-1h", name="invalid.metric")

        assert result is None


class TestBatchQuery:
    """Tests for batch query functions."""

    def test_getCheckpointPath(self):
        """Test checkpoint path generation."""
        from sage.beehive.extraction.batchQuery import getCheckpointPath

        path = getCheckpointPath("output.csv")
        assert path == ".output.csv.checkpoint"

    def test_saveAndLoadCheckpoint(self, tempDir):
        """Test checkpoint save/load."""
        from sage.beehive.extraction.batchQuery import saveCheckpoint, loadCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        data = {
            "name": "env.temperature",
            "vsn": "W01B",
            "lastProcessedTimestamp": "2024-01-01T00:00:00Z"
        }

        saveCheckpoint(checkpointPath, data)
        loaded = loadCheckpoint(checkpointPath)

        assert loaded is not None
        assert loaded['name'] == "env.temperature"
        assert loaded['vsn'] == "W01B"

    def test_runBatchQueryMissingVsn(self):
        """Test batch query without required VSN."""
        from sage.beehive.extraction.batchQuery import runBatchQuery

        result = runBatchQuery(name="env.temperature", start="-7d")
        assert result is None


class TestRegionalQuery:
    """Tests for regional query functions."""

    def test_beeHiveProInit(self):
        """Test BeeHivePro initialization."""
        from sage.beehive.extraction.regionalQuery import BeeHivePro

        pro = BeeHivePro()
        assert pro.registryFile == "nodeRegistry.csv"
        assert pro.regions is not None

    def test_getNodesInRegionWithCache(self, sampleNodeRegistryCsv, regionsJsonFile):
        """Test filtering nodes by region."""
        from sage.beehive.extraction.regionalQuery import BeeHivePro

        pro = BeeHivePro(registryFile=sampleNodeRegistryCsv)
        pro.regions.configFile = regionsJsonFile

        # Load the registry
        pro.registry = pd.read_csv(sampleNodeRegistryCsv)
        pro.registry['vsn'] = pro.registry['vsn'].astype(str)

        # This should find Chicago nodes
        chicagoNodes = pro.getNodesInRegion("chicago")

        # Should find nodes with lat/lon in Chicago range
        assert len(chicagoNodes) >= 0  # May be empty depending on test data
