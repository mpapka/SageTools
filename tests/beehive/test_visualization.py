"""
Tests for sage.beehive.visualization module.
"""

import pytest
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for tests


class TestPlotTemperature:
    """Tests for plotTemperature function."""

    def test_plotTemperatureSuccess(self, sampleCsvFile, tempDir):
        """Test plotting temperature data."""
        outputFile = os.path.join(tempDir, "test_plot.png")

        from sage.beehive.visualization.plotTemperature import plotTemperature
        result = plotTemperature(sampleCsvFile, output=outputFile)

        assert result is True
        assert os.path.exists(outputFile)

    def test_plotTemperatureFileNotFound(self, tempDir):
        """Test plotting with non-existent file."""
        from sage.beehive.visualization.plotTemperature import plotTemperature
        result = plotTemperature(os.path.join(tempDir, "nonexistent.csv"))

        assert result is False


class TestPlotComparison:
    """Tests for plotComparison function."""

    def test_plotComparisonSuccess(self, tempDir, sampleTemperatureDf):
        """Test comparison plot with multiple files."""
        # Create two test files
        file1 = os.path.join(tempDir, "test1.csv")
        file2 = os.path.join(tempDir, "test2.csv")

        df1 = sampleTemperatureDf.copy()
        df1['meta.vsn'] = 'W01B'
        df1.to_csv(file1, index=False)

        df2 = sampleTemperatureDf.copy()
        df2['meta.vsn'] = 'W01C'
        df2['value'] = df2['value'] + 5  # Slightly different values
        df2.to_csv(file2, index=False)

        outputFile = os.path.join(tempDir, "comparison.png")

        from sage.beehive.visualization.plotComparison import plotComparison
        result = plotComparison([file1, file2], output=outputFile)

        assert result is True
        assert os.path.exists(outputFile)


class TestPlotLifetimes:
    """Tests for plotLifetimes function."""

    def test_plotLifetimesSuccess(self, sampleNodeRegistryCsv, tempDir):
        """Test lifetime plot."""
        outputFile = os.path.join(tempDir, "lifetimes.png")

        from sage.beehive.visualization.plotLifetimes import plotLifetimes
        result = plotLifetimes(sampleNodeRegistryCsv, output=outputFile)

        assert result is True
        assert os.path.exists(outputFile)

    def test_plotLifetimesWithFilters(self, sampleNodeRegistryCsv, tempDir):
        """Test lifetime plot with filters."""
        outputFile = os.path.join(tempDir, "lifetimes_filtered.png")

        from sage.beehive.visualization.plotLifetimes import plotLifetimes
        result = plotLifetimes(sampleNodeRegistryCsv, output=outputFile, prefix="W")

        # Should succeed with filtered nodes
        assert result is True

    def test_plotLifetimesFileNotFound(self, tempDir):
        """Test with non-existent registry file."""
        from sage.beehive.visualization.plotLifetimes import plotLifetimes
        result = plotLifetimes(os.path.join(tempDir, "nonexistent.csv"))

        assert result is False
