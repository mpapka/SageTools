"""
CSV utilities for Sage Beehive data processing.

Provides functions for fixing, aligning, and standardizing CSV files that may
have inconsistent column structures due to incremental data collection.
"""

import os
import pandas as pd
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

console = Console()


def alignColumns(df: pd.DataFrame, targetColumns: list) -> pd.DataFrame:
    """
    Align DataFrame columns to match a target column list.

    Adds missing columns (with NaN values) and removes extra columns.
    This ensures consistency when appending data to an existing file.

    Args:
        df: DataFrame to align
        targetColumns: List of column names to match

    Returns:
        DataFrame with aligned columns
    """
    return df.reindex(columns=targetColumns)


def getExistingColumns(filepath: str) -> Optional[list]:
    """
    Get column headers from an existing CSV file.

    Args:
        filepath: Path to CSV file

    Returns:
        List of column names, or None if file doesn't exist
    """
    if not os.path.exists(filepath):
        return None

    try:
        return pd.read_csv(filepath, nrows=0).columns.tolist()
    except Exception:
        return None


def fixCsv(inputFile: str, outputFile: str = None, progress: Progress = None) -> bool:
    """
    Fix a CSV file with inconsistent column structure.

    Scans the entire file to discover all columns, then rewrites with
    consistent column structure.

    Args:
        inputFile: Path to input CSV file
        outputFile: Path for output (default: inputFile with _fixed suffix)
        progress: Optional Progress instance for nested progress tracking

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(inputFile):
        console.print(f"[red]Error: {inputFile} not found.[/red]")
        return False

    if outputFile is None:
        outputFile = inputFile.replace(".csv", "_fixed.csv")

    # Estimate row count from file size
    fileSize = os.path.getsize(inputFile)
    estimatedRows = fileSize // 250  # Average Beehive row is ~250 bytes

    chunkSize = 500000

    try:
        # Phase 1: Column Discovery
        console.print(f"[cyan]Scanning {os.path.basename(inputFile)} for columns...[/cyan]")
        allColumns = set()
        totalRows = 0

        for chunk in pd.read_csv(inputFile, chunksize=chunkSize, low_memory=False, on_bad_lines='skip'):
            allColumns.update(chunk.columns)
            totalRows += len(chunk)

        colList = sorted(list(allColumns))
        console.print(f"[green]Found {len(colList)} unique columns across {totalRows:,} rows[/green]")

        # Phase 2: Rewrite with consistent columns
        if os.path.exists(outputFile):
            os.remove(outputFile)

        console.print(f"[cyan]Writing standardized output to {os.path.basename(outputFile)}...[/cyan]")
        firstChunk = True
        processedRows = 0

        for chunk in pd.read_csv(inputFile, chunksize=chunkSize, low_memory=False, on_bad_lines='skip'):
            chunk = chunk.reindex(columns=colList)
            chunk.to_csv(outputFile, mode='a', index=False, header=firstChunk)
            firstChunk = False
            processedRows += len(chunk)

        console.print(f"[green]Successfully fixed {inputFile} -> {outputFile}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Failed to fix {inputFile}: {e}[/red]")
        return False


def batchFixCsv(files: list) -> int:
    """
    Fix multiple CSV files with progress tracking.

    Args:
        files: List of file paths to fix

    Returns:
        Number of successfully fixed files
    """
    console.print(f"[bold cyan]Beehive CSV Format Standardizer[/bold cyan]")
    console.print(f"Unifying metadata columns across {len(files)} files.\n")

    successCount = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        refresh_per_second=2
    ) as progress:
        mainTask = progress.add_task("[bold yellow]Batch Progress", total=len(files))

        for filepath in files:
            if fixCsv(filepath, progress=progress):
                successCount += 1
            progress.advance(mainTask)

    console.print(f"\n[bold green]{successCount}/{len(files)} files processed successfully![/bold green]")
    return successCount


def mergeCsvFiles(inputFiles: list, outputFile: str, dedup: bool = False) -> bool:
    """
    Merge multiple CSV files into one with consistent columns.

    Args:
        inputFiles: List of CSV file paths to merge
        outputFile: Output file path
        dedup: If True, remove duplicate rows

    Returns:
        True if successful
    """
    try:
        # Discover all columns
        allColumns = set()
        for filepath in inputFiles:
            if os.path.exists(filepath):
                cols = getExistingColumns(filepath)
                if cols:
                    allColumns.update(cols)

        colList = sorted(list(allColumns))

        # Write merged file
        firstFile = True
        for filepath in inputFiles:
            if not os.path.exists(filepath):
                continue

            for chunk in pd.read_csv(filepath, chunksize=500000, low_memory=False, on_bad_lines='skip'):
                chunk = chunk.reindex(columns=colList)
                if dedup:
                    chunk = chunk.drop_duplicates()
                chunk.to_csv(outputFile, mode='a', index=False, header=firstFile)
                firstFile = False

        console.print(f"[green]Merged {len(inputFiles)} files to {outputFile}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Failed to merge files: {e}[/red]")
        return False
