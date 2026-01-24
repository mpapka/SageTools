#!/usr/bin/env python3
"""
Batch Sage Beehive data query with adaptive chunking and resume support.

Handles large time ranges by breaking them into manageable chunks and
automatically retrying with smaller chunks on server errors.
"""

import sage_data_client
import argparse
import pandas as pd
import os
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parseDate
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

from ...common.csvUtils import alignColumns, getExistingColumns

console = Console()


def getCheckpointPath(outputFile: str) -> str:
    """Generate checkpoint file path from output file name."""
    return f".{outputFile}.checkpoint"


def saveCheckpoint(checkpointPath: str, data: dict):
    """Save checkpoint data to file."""
    with open(checkpointPath, 'w') as f:
        json.dump(data, f)


def loadCheckpoint(checkpointPath: str) -> Optional[dict]:
    """Load checkpoint data if it exists."""
    if os.path.exists(checkpointPath):
        with open(checkpointPath, 'r') as f:
            return json.load(f)
    return None


def runBatchQuery(
    name: str = "env.temperature",
    vsn: str = None,
    start: str = None,
    end: str = "now",
    chunkSize: str = "7d",
    output: str = None,
    reset: bool = False
) -> Optional[str]:
    """
    Query Sage Beehive data in adaptive batches with resume support.

    Args:
        name: Metric name (e.g., "env.temperature")
        vsn: VSN of the node (required)
        start: Start time (e.g., "2023-01-01" or "-30d")
        end: End time (default: "now")
        chunkSize: Target chunk size (e.g., "1h", "1d", "7d")
        output: Output CSV filename (auto-generated if not provided)
        reset: Ignore existing checkpoint and start fresh

    Returns:
        Output filename on success, None on error
    """
    if vsn is None:
        console.print("[red]Error: VSN is required[/red]")
        return None

    if start is None:
        console.print("[red]Error: Start time is required[/red]")
        return None

    # Determine end time - always make it UTC aware
    if end == "now":
        endTime = datetime.now(timezone.utc)
    else:
        endTime = parseDate(end)
        if endTime.tzinfo is None:
            endTime = endTime.replace(tzinfo=timezone.utc)

    # Parse start time
    if start.startswith("-"):
        unit = start[-1]
        value = int(start[1:-1])
        if unit == 'h':
            startTime = endTime - timedelta(hours=value)
        elif unit == 'd':
            startTime = endTime - timedelta(days=value)
        elif unit == 'w':
            startTime = endTime - timedelta(weeks=value)
        elif unit == 'y':
            startTime = endTime - timedelta(days=365*value)
        else:
            startTime = endTime - timedelta(hours=1)
    else:
        startTime = parseDate(start)
        if startTime.tzinfo is None:
            startTime = startTime.replace(tzinfo=timezone.utc)

    # Generate output filename
    metricName = name.replace('.', ' ').title().replace(' ', '')
    metricName = metricName[0].lower() + metricName[1:]
    outputFile = output if output else f"{metricName}{vsn}Batch.csv"
    checkpointPath = getCheckpointPath(outputFile)

    # Check for existing checkpoint
    checkpoint = loadCheckpoint(checkpointPath)
    if checkpoint and not reset:
        if checkpoint['name'] == name and checkpoint['vsn'] == vsn:
            startTime = parseDate(checkpoint['lastProcessedTimestamp'])
            if startTime.tzinfo is None:
                startTime = startTime.replace(tzinfo=timezone.utc)
            console.print(f"[green]Resuming from {startTime.strftime('%Y-%m-%d')}[/green]")

    # Target duration parsing
    unit = chunkSize[-1]
    value = int(chunkSize[:-1])
    if unit == 'h':
        targetDuration = timedelta(hours=value)
    elif unit == 'd':
        targetDuration = timedelta(days=value)
    elif unit == 'w':
        targetDuration = timedelta(weeks=value)
    else:
        targetDuration = timedelta(hours=1)

    minDuration = timedelta(hours=1)
    currentDuration = targetDuration

    totalDurationSecs = (endTime - startTime).total_seconds()

    console.print(f"[bold blue]Node:[/bold blue] {vsn} | [bold blue]Metric:[/bold blue] {name}")
    console.print(f"[bold blue]Range:[/bold blue] {startTime.date()} to {endTime.date()}")
    console.print(f"[bold blue]Target Chunk:[/bold blue] {chunkSize}")

    currentStart = startTime
    totalRecords = 0
    writeHeader = not os.path.exists(outputFile)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        refresh_per_second=1
    ) as progress:

        mainTask = progress.add_task(f"Downloading {vsn}", total=totalDurationSecs)

        while currentStart < endTime:
            currentEnd = min(currentStart + currentDuration, endTime)
            startStr = currentStart.strftime('%Y-%m-%dT%H:%M:%SZ')
            endStr = currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ')

            try:
                # Update task description to show current chunk size
                durDays = currentDuration.total_seconds() / 86400
                progress.update(mainTask, description=f"Downloading {vsn} ({durDays:.1f}d chunk)")

                df = sage_data_client.query(
                    start=startStr,
                    end=endStr,
                    filter={"name": name, "vsn": vsn}
                )

                if not df.empty:
                    # Column Alignment Logic: Ensure the chunk matches the existing file structure
                    existingCols = getExistingColumns(outputFile)
                    if existingCols and not writeHeader:
                        df = alignColumns(df, existingCols)

                    df.to_csv(outputFile, mode='a', index=False, header=writeHeader)
                    writeHeader = False
                    totalRecords += len(df)

                saveCheckpoint(checkpointPath, {
                    "name": name,
                    "vsn": vsn,
                    "lastProcessedTimestamp": endStr,
                    "outputFile": outputFile,
                    "chunkSize": chunkSize
                })

                # Success! Move forward and slightly increase chunk size if below target
                chunkSecs = (currentEnd - currentStart).total_seconds()
                progress.advance(mainTask, chunkSecs)
                currentStart = currentEnd

                if currentDuration < targetDuration:
                    currentDuration = min(currentDuration * 2, targetDuration)

            except Exception as e:
                # Failure! Shrink chunk size and retry same window
                if "500" in str(e) and currentDuration > minDuration:
                    progress.console.print(f"[yellow]Window {startStr} failed (500). Halving chunk size and retrying...[/yellow]")
                    currentDuration = max(currentDuration / 2, minDuration)
                    # Don't advance currentStart, loop will retry with new currentDuration
                    time.sleep(1)
                else:
                    console.print(f"\n[bold red]Fatal error at {startStr}:[/bold red] {e}")
                    return None

    # Clear checkpoint on success
    if os.path.exists(checkpointPath):
        os.remove(checkpointPath)

    console.print(f"[bold green]Done![/bold green] Total records this session: [yellow]{totalRecords}[/yellow]")
    console.print(f"Output saved to: [cyan]{outputFile}[/cyan]")

    return outputFile


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Query Sage Beehive data in adaptive batches with resume support.")
    parser.add_argument("--name", default="env.temperature", help="Metric name")
    parser.add_argument("--vsn", required=True, help="VSN of the node (e.g., W077)")
    parser.add_argument("--start", required=True, help="Start time (e.g., 2023-01-01 or -30d)")
    parser.add_argument("--end", default="now", help="End time (default: now)")
    parser.add_argument("--chunkSize", default="7d", help="Target chunk size (e.g., 1h, 1d, 7d)")
    parser.add_argument("--output", help="Output CSV filename")
    parser.add_argument("--reset", action="store_true", help="Ignore existing checkpoint and start fresh")

    args = parser.parse_args()

    runBatchQuery(
        name=args.name,
        vsn=args.vsn,
        start=args.start,
        end=args.end,
        chunkSize=args.chunkSize,
        output=args.output,
        reset=args.reset
    )


if __name__ == "__main__":
    main()
