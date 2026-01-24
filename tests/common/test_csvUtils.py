"""
Tests for sage.common.csvUtils module.
"""

import pytest
import pandas as pd
import os


class TestAlignColumns:
    """Tests for column alignment function."""

    def test_alignColumnsAddsMissing(self):
        """Test that missing columns are added."""
        from sage.common.csvUtils import alignColumns

        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        targetCols = ['a', 'b', 'c']

        result = alignColumns(df, targetCols)

        assert 'c' in result.columns
        assert result['c'].isna().all()

    def test_alignColumnsRemovesExtra(self):
        """Test that extra columns are removed."""
        from sage.common.csvUtils import alignColumns

        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        targetCols = ['a', 'b']

        result = alignColumns(df, targetCols)

        assert 'c' not in result.columns
        assert list(result.columns) == ['a', 'b']

    def test_alignColumnsPreservesOrder(self):
        """Test that column order matches target."""
        from sage.common.csvUtils import alignColumns

        df = pd.DataFrame({'c': [1], 'a': [2], 'b': [3]})
        targetCols = ['a', 'b', 'c']

        result = alignColumns(df, targetCols)

        assert list(result.columns) == ['a', 'b', 'c']


class TestGetExistingColumns:
    """Tests for getting columns from existing CSV."""

    def test_getExistingColumnsSuccess(self, sampleCsvFile):
        """Test getting columns from existing file."""
        from sage.common.csvUtils import getExistingColumns

        cols = getExistingColumns(sampleCsvFile)

        assert cols is not None
        assert 'timestamp' in cols
        assert 'value' in cols

    def test_getExistingColumnsNotExists(self, tempDir):
        """Test getting columns from non-existent file."""
        from sage.common.csvUtils import getExistingColumns

        result = getExistingColumns(os.path.join(tempDir, "nonexistent.csv"))

        assert result is None


class TestFixCsv:
    """Tests for CSV fixing function."""

    def test_fixCsvSuccess(self, tempDir):
        """Test fixing a CSV with inconsistent columns."""
        # Create a file with varying columns per chunk
        inputPath = os.path.join(tempDir, "input.csv")
        outputPath = os.path.join(tempDir, "input_fixed.csv")

        # Create file with all columns
        df = pd.DataFrame({
            'timestamp': ['2024-01-01', '2024-01-02'],
            'value': [1, 2],
            'extra': ['a', 'b']
        })
        df.to_csv(inputPath, index=False)

        from sage.common.csvUtils import fixCsv

        result = fixCsv(inputPath)

        assert result is True
        assert os.path.exists(outputPath)

        # Verify output has consistent columns
        fixed = pd.read_csv(outputPath)
        assert 'timestamp' in fixed.columns
        assert 'value' in fixed.columns

    def test_fixCsvNotFound(self, tempDir):
        """Test fixing non-existent file."""
        from sage.common.csvUtils import fixCsv

        result = fixCsv(os.path.join(tempDir, "nonexistent.csv"))

        assert result is False

    def test_fixCsvCustomOutput(self, sampleCsvFile, tempDir):
        """Test fixing with custom output path."""
        outputPath = os.path.join(tempDir, "custom_output.csv")

        from sage.common.csvUtils import fixCsv

        result = fixCsv(sampleCsvFile, outputFile=outputPath)

        assert result is True
        assert os.path.exists(outputPath)


class TestMergeCsvFiles:
    """Tests for merging CSV files."""

    def test_mergeCsvFilesSuccess(self, tempDir):
        """Test merging multiple CSV files."""
        # Create two files with different columns
        file1 = os.path.join(tempDir, "file1.csv")
        file2 = os.path.join(tempDir, "file2.csv")
        outputFile = os.path.join(tempDir, "merged.csv")

        pd.DataFrame({'a': [1, 2], 'b': [3, 4]}).to_csv(file1, index=False)
        pd.DataFrame({'a': [5, 6], 'c': [7, 8]}).to_csv(file2, index=False)

        from sage.common.csvUtils import mergeCsvFiles

        result = mergeCsvFiles([file1, file2], outputFile)

        assert result is True
        assert os.path.exists(outputFile)

        merged = pd.read_csv(outputFile)
        assert len(merged) == 4
        assert 'a' in merged.columns
        assert 'b' in merged.columns
        assert 'c' in merged.columns

    def test_mergeCsvFilesWithDedup(self, tempDir):
        """Test merging with deduplication."""
        file1 = os.path.join(tempDir, "file1.csv")
        outputFile = os.path.join(tempDir, "merged.csv")

        # File with duplicates
        pd.DataFrame({'a': [1, 1, 2], 'b': [3, 3, 4]}).to_csv(file1, index=False)

        from sage.common.csvUtils import mergeCsvFiles

        result = mergeCsvFiles([file1], outputFile, dedup=True)

        assert result is True

        merged = pd.read_csv(outputFile)
        assert len(merged) == 2  # Duplicates removed
