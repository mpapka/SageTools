"""
Checkpoint utilities for resumable operations.

Provides save/load functionality for long-running operations that may need
to be interrupted and resumed later.
"""

import os
import json
import pickle
from datetime import datetime
from typing import Any, Optional

from rich.console import Console

console = Console()


def getCheckpointPath(outputFile: str) -> str:
    """
    Generate checkpoint file path from output file name.

    Args:
        outputFile: The output file name

    Returns:
        Checkpoint file path (hidden file with .checkpoint extension)
    """
    return f".{outputFile}.checkpoint"


def saveCheckpoint(checkpointPath: str, data: dict) -> bool:
    """
    Save checkpoint data to a file.

    Supports both JSON (for simple data) and pickle (for complex objects like DataFrames).

    Args:
        checkpointPath: Path to save checkpoint
        data: Dictionary containing checkpoint data

    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Add timestamp to checkpoint
        data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Try JSON first (smaller, human-readable)
        if _isJsonSerializable(data):
            with open(checkpointPath, 'w') as f:
                json.dump(data, f)
        else:
            # Fall back to pickle for complex objects
            with open(checkpointPath, 'wb') as f:
                pickle.dump(data, f)
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save checkpoint: {e}[/yellow]")
        return False


def loadCheckpoint(checkpointPath: str) -> Optional[dict]:
    """
    Load checkpoint data from a file.

    Automatically detects JSON vs pickle format.

    Args:
        checkpointPath: Path to checkpoint file

    Returns:
        Checkpoint data dictionary, or None if not found/invalid
    """
    if not os.path.exists(checkpointPath):
        return None

    try:
        # Try JSON first
        with open(checkpointPath, 'r') as f:
            data = json.load(f)
            console.print(f"[green]Found checkpoint from {data.get('timestamp', 'unknown time')}[/green]")
            return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    try:
        # Try pickle
        with open(checkpointPath, 'rb') as f:
            data = pickle.load(f)
            console.print(f"[green]Found checkpoint from {data.get('timestamp', 'unknown time')}[/green]")
            return data
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load checkpoint: {e}[/yellow]")
        return None


def clearCheckpoint(checkpointPath: str) -> bool:
    """
    Remove checkpoint file after successful completion.

    Args:
        checkpointPath: Path to checkpoint file

    Returns:
        True if removed or didn't exist, False on error
    """
    try:
        if os.path.exists(checkpointPath):
            os.remove(checkpointPath)
            console.print("[green]Checkpoint cleared[/green]")
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not clear checkpoint: {e}[/yellow]")
        return False


def _isJsonSerializable(data: Any) -> bool:
    """Check if data can be serialized to JSON."""
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False
