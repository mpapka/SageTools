"""
Tests for sage.common.regions module.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock


class TestRegionManager:
    """Tests for RegionManager class."""

    def test_initWithDefaults(self, tempDir):
        """Test initialization creates default regions."""
        configPath = os.path.join(tempDir, "regions.json")

        from sage.common.regions import RegionManager

        manager = RegionManager(configPath)

        assert 'usa' in manager.regions
        assert 'chicago' in manager.regions
        assert os.path.exists(configPath)

    def test_initWithExisting(self, regionsJsonFile):
        """Test initialization loads existing config."""
        from sage.common.regions import RegionManager

        manager = RegionManager(regionsJsonFile)

        assert 'usa' in manager.regions
        assert 'chicago' in manager.regions

    def test_getBboxCached(self, regionsJsonFile):
        """Test getting cached region."""
        from sage.common.regions import RegionManager

        manager = RegionManager(regionsJsonFile)
        bbox = manager.getBbox("chicago")

        assert bbox is not None
        assert 'lat' in bbox
        assert 'lon' in bbox
        assert len(bbox['lat']) == 2
        assert len(bbox['lon']) == 2

    def test_getBboxNormalized(self, regionsJsonFile):
        """Test region name normalization."""
        from sage.common.regions import RegionManager

        manager = RegionManager(regionsJsonFile)

        # Should work with different cases and spaces
        bbox1 = manager.getBbox("Chicago")
        bbox2 = manager.getBbox("CHICAGO")
        bbox3 = manager.getBbox("chicago")

        assert bbox1 == bbox2 == bbox3

    def test_getBboxOnlineLookup(self, tempDir):
        """Test online lookup via Nominatim (mocked)."""
        configPath = os.path.join(tempDir, "regions.json")

        from sage.common.regions import RegionManager

        manager = RegionManager(configPath)

        # Mock the online lookup
        mockResponse = MagicMock()
        mockResponse.read.return_value = json.dumps([{
            'boundingbox': ['40.0', '42.0', '-90.0', '-87.0']
        }]).encode()
        mockResponse.__enter__ = MagicMock(return_value=mockResponse)
        mockResponse.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mockResponse):
            bbox = manager.getBbox("Springfield")

        assert bbox is not None
        assert bbox['lat'] == [40.0, 42.0]
        assert bbox['lon'] == [-90.0, -87.0]

        # Should be cached now
        assert 'springfield' in manager.regions

    def test_getBboxNotFound(self, tempDir):
        """Test online lookup failure."""
        configPath = os.path.join(tempDir, "regions.json")

        from sage.common.regions import RegionManager

        manager = RegionManager(configPath)

        with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
            bbox = manager.getBbox("NonexistentPlace12345")

        assert bbox is None


class TestRegionManagerManual:
    """Tests for manual region management."""

    def test_addRegion(self, tempDir):
        """Test manually adding a region."""
        configPath = os.path.join(tempDir, "regions.json")

        from sage.common.regions import RegionManager

        manager = RegionManager(configPath)
        result = manager.addRegion("test_area", [30.0, 35.0], [-100.0, -95.0])

        assert result is True
        assert 'test_area' in manager.regions
        assert manager.regions['test_area']['lat'] == [30.0, 35.0]

    def test_removeRegion(self, tempDir):
        """Test removing a region."""
        configPath = os.path.join(tempDir, "regions.json")

        from sage.common.regions import RegionManager

        manager = RegionManager(configPath)
        manager.addRegion("to_remove", [0, 1], [0, 1])
        assert 'to_remove' in manager.regions

        result = manager.removeRegion("to_remove")
        assert result is True
        assert 'to_remove' not in manager.regions

    def test_listRegions(self, regionsJsonFile):
        """Test listing all regions."""
        from sage.common.regions import RegionManager

        manager = RegionManager(regionsJsonFile)
        regions = manager.listRegions()

        assert 'usa' in regions
        assert 'chicago' in regions
