"""
Tests for sage.common.checkpoints module.
"""

import pytest
import os
import json


class TestCheckpointPath:
    """Tests for checkpoint path generation."""

    def test_getCheckpointPath(self):
        """Test checkpoint path generation."""
        from sage.common.checkpoints import getCheckpointPath

        path = getCheckpointPath("output.csv")
        assert path == ".output.csv.checkpoint"

        path = getCheckpointPath("data/results.csv")
        assert path == ".data/results.csv.checkpoint"


class TestSaveCheckpoint:
    """Tests for checkpoint saving."""

    def test_saveCheckpointJson(self, tempDir):
        """Test saving JSON-serializable checkpoint."""
        from sage.common.checkpoints import saveCheckpoint, loadCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        result = saveCheckpoint(checkpointPath, data)
        assert result is True
        assert os.path.exists(checkpointPath)

        # Verify it was saved as JSON
        with open(checkpointPath, 'r') as f:
            loaded = json.load(f)
            assert loaded['key'] == "value"

    def test_saveCheckpointPickle(self, tempDir):
        """Test saving non-JSON-serializable checkpoint (uses pickle)."""
        import pandas as pd
        from sage.common.checkpoints import saveCheckpoint, loadCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        data = {"dataframe": pd.DataFrame({'a': [1, 2, 3]})}

        result = saveCheckpoint(checkpointPath, data)
        assert result is True
        assert os.path.exists(checkpointPath)


class TestLoadCheckpoint:
    """Tests for checkpoint loading."""

    def test_loadCheckpointJson(self, tempDir):
        """Test loading JSON checkpoint."""
        from sage.common.checkpoints import saveCheckpoint, loadCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        originalData = {"key": "value", "timestamp": "2024-01-01"}

        saveCheckpoint(checkpointPath, originalData)
        loaded = loadCheckpoint(checkpointPath)

        assert loaded is not None
        assert loaded['key'] == "value"

    def test_loadCheckpointNotExists(self, tempDir):
        """Test loading non-existent checkpoint."""
        from sage.common.checkpoints import loadCheckpoint

        result = loadCheckpoint(os.path.join(tempDir, "nonexistent"))
        assert result is None

    def test_loadCheckpointPickle(self, tempDir):
        """Test loading pickle checkpoint."""
        import pandas as pd
        from sage.common.checkpoints import saveCheckpoint, loadCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        originalData = {"dataframe": df}

        saveCheckpoint(checkpointPath, originalData)
        loaded = loadCheckpoint(checkpointPath)

        assert loaded is not None
        assert 'dataframe' in loaded
        assert len(loaded['dataframe']) == 3


class TestClearCheckpoint:
    """Tests for checkpoint clearing."""

    def test_clearCheckpointExists(self, tempDir):
        """Test clearing existing checkpoint."""
        from sage.common.checkpoints import saveCheckpoint, clearCheckpoint

        checkpointPath = os.path.join(tempDir, ".test.checkpoint")
        saveCheckpoint(checkpointPath, {"key": "value"})
        assert os.path.exists(checkpointPath)

        result = clearCheckpoint(checkpointPath)
        assert result is True
        assert not os.path.exists(checkpointPath)

    def test_clearCheckpointNotExists(self, tempDir):
        """Test clearing non-existent checkpoint."""
        from sage.common.checkpoints import clearCheckpoint

        result = clearCheckpoint(os.path.join(tempDir, "nonexistent"))
        assert result is True  # Should succeed silently
