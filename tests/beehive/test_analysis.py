"""
Tests for sage.beehive.analysis module.
"""

import pytest
import pandas as pd
import os
from datetime import datetime


class TestStatistics:
    """Tests for statistics analysis functions."""

    def test_analyzeFileSuccess(self, sampleCsvFile):
        """Test analyzing a valid CSV file."""
        from sage.beehive.analysis.statistics import analyzeFile

        result = analyzeFile(sampleCsvFile)

        assert result is not None
        assert 'vsn' in result
        assert 'minF' in result
        assert 'maxF' in result
        assert 'avgF' in result
        assert 'count' in result
        assert result['count'] > 0

    def test_analyzeFileNotFound(self, tempDir):
        """Test analyzing non-existent file."""
        from sage.beehive.analysis.statistics import analyzeFile

        result = analyzeFile(os.path.join(tempDir, "nonexistent.csv"))
        assert result is None

    def test_temperatureConversion(self, tempDir):
        """Test that Celsius to Fahrenheit conversion is correct."""
        # Create a simple file with known values
        filepath = os.path.join(tempDir, "conversion_test.csv")
        df = pd.DataFrame({
            'value': [0, 100, -40],  # 32F, 212F, -40F
            'meta.sensor': ['test', 'test', 'test'],
        })
        df.to_csv(filepath, index=False)

        from sage.beehive.analysis.statistics import analyzeFile
        result = analyzeFile(filepath)

        assert result is not None
        assert result['minF'] == pytest.approx(-40.0)  # -40C = -40F
        assert result['maxF'] == pytest.approx(212.0)  # 100C = 212F


class TestSensorAudit:
    """Tests for sensor audit functions."""

    def test_auditFileDetectsFailures(self, tempDir):
        """Test that audit detects sensor failures."""
        # Create file with extreme values
        filepath = os.path.join(tempDir, "audit_test.csv")
        df = pd.DataFrame({
            'value': [25, 25, -100, 200],  # Last two are failures
            'meta.sensor': ['good', 'good', 'bad', 'bad'],
            'meta.host': ['host1', 'host1', 'host2', 'host2'],
        })
        df.to_csv(filepath, index=False)

        from sage.beehive.analysis.sensorAudit import auditFile
        results = auditFile(filepath)

        # Should have results for both sensors
        assert len(results) == 2

        # Find the bad sensor
        badSensor = [r for r in results if r['sensor'] == 'bad']
        assert len(badSensor) == 1
        assert 'FAIL' in badSensor[0]['reliability'] or badSensor[0]['reliability'] != 'GOOD'


class TestTuneBatch:
    """Tests for tune batch benchmark."""

    def test_benchmarkHandlesErrors(self, mockSageDataClient):
        """Test that benchmark handles API errors gracefully."""
        # Make all queries fail
        mockSageDataClient.side_effect = Exception("500 Internal Server Error")

        from sage.beehive.analysis.tuneBatch import benchmark
        result = benchmark(vsn="W01B")

        assert result is not None
        assert 'results' in result
        # All should have failed
        for r in result['results']:
            assert r['success'] is False
