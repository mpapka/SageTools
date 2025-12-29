#!/usr/bin/env python3
import sage_data_client
import argparse
import pandas as pd
import os
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parseDate
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

console = Console()

def getCheckpointPath(outputFile):
    return f".{outputFile}.checkpoint"

def saveCheckpoint(checkpointPath, data):
    with open(checkpointPath, 'w') as f:
        json.dump(data, f)

def loadCheckpoint(checkpointPath):
    if os.path.exists(checkpointPath):
        with open(checkpointPath, 'r') as f:
            return json.load(f)
    return None

def runBatchQuery():
    parser = argparse.ArgumentParser(description="Query Sage Beehive data in adaptive batches with resume support.")
    parser.add_argument("--name", default="env.temperature", help="Metric name")
    parser.add_argument("--vsn", required=True, help="VSN of the node (e.g. W077)")
    parser.add_argument("--start", required=True, help="Start time (e.g. 2023-01-01 or -30d)")
    parser.add_argument("--end", default="now", help="End time (default: now)")
    parser.add_argument("--chunkSize", default="7d", help="Target chunk size (e.g. 1h, 1d, 7d)")
    parser.add_argument("--output", help="Output CSV filename")
    parser.add_argument("--reset", action="store_true", help="Ignore existing checkpoint and start fresh")

    args = parser.parse_args()

    # Determine end time - always make it UTC aware
    if args.end == "now":
        endTime = datetime.now(timezone.utc)
    else:
        endTime = parseDate(args.end)
        if endTime.tzinfo is None:
            endTime = endTime.replace(tzinfo=timezone.utc)
    
    if args.start.startswith("-"):
        unit = args.start[-1]
        value = int(args.start[1:-1])
        if unit == 'h': startTime = endTime - timedelta(hours=value)
        elif unit == 'd': startTime = endTime - timedelta(days=value)
        elif unit == 'w': startTime = endTime - timedelta(weeks=value)
        elif unit == 'y': startTime = endTime - timedelta(days=365*value)
        else: startTime = endTime - timedelta(hours=1)
    else:
        startTime = parseDate(args.start)
        if startTime.tzinfo is None:
            startTime = startTime.replace(tzinfo=timezone.utc)

    metricName = args.name.replace('.', ' ').title().replace(' ', '')
    metricName = metricName[0].lower() + metricName[1:]
    outputFile = args.output if args.output else f"{metricName}{args.vsn}Batch.csv"
    checkpointPath = getCheckpointPath(outputFile)
    
    checkpoint = loadCheckpoint(checkpointPath)
    if checkpoint and not args.reset:
        if checkpoint['name'] == args.name and checkpoint['vsn'] == args.vsn:
            startTime = parseDate(checkpoint['lastProcessedTimestamp'])
            if startTime.tzinfo is None:
                startTime = startTime.replace(tzinfo=timezone.utc)
    
    # Target duration parsing
    unit = args.chunkSize[-1]
    value = int(args.chunkSize[:-1])
    if unit == 'h': targetDuration = timedelta(hours=value)
    elif unit == 'd': targetDuration = timedelta(days=value)
    elif unit == 'w': targetDuration = timedelta(weeks=value)
    else: targetDuration = timedelta(hours=1)

    minDuration = timedelta(hours=1)
    currentDuration = targetDuration
    
    totalDurationSecs = (endTime - startTime).total_seconds()
    
    console.print(f"[bold blue]Node:[/bold blue] {args.vsn} | [bold blue]Metric:[/bold blue] {args.name}")
    console.print(f"[bold blue]Range:[/bold blue] {startTime.date()} to {endTime.date()}")
    console.print(f"[bold blue]Target Chunk:[/bold blue] {args.chunkSize}")
    
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
        
        mainTask = progress.add_task(f"Downloading {args.vsn}", total=totalDurationSecs)

        while currentStart < endTime:
            currentEnd = min(currentStart + currentDuration, endTime)
            startStr = currentStart.strftime('%Y-%m-%dT%H:%M:%SZ')
            endStr = currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            try:
                # Update task description to show current chunk size
                durDays = currentDuration.total_seconds() / 86400
                progress.update(mainTask, description=f"Downloading {args.vsn} ({durDays:.1f}d chunk)")
                
                df = sage_data_client.query(
                    start=startStr,
                    end=endStr,
                    filter={"name": args.name, "vsn": args.vsn}
                )
                
                if not df.empty:
                    # Column Alignment Logic: Ensure the chunk matches the existing file structure
                    if os.path.exists(outputFile) and not writeHeader:
                        # Read only the header of the existing file
                        existingHeader = pd.read_csv(outputFile, nrows=0).columns.tolist()
                        # Reindex the new dataframe to match the existing columns
                        # This adds NaNs for missing columns and drops extra columns
                        df = df.reindex(columns=existingHeader)
                    
                    df.to_csv(outputFile, mode='a', index=False, header=writeHeader)
                    writeHeader = False
                    totalRecords += len(df)
                
                saveCheckpoint(checkpointPath, {
                    "name": args.name,
                    "vsn": args.vsn,
                    "lastProcessedTimestamp": endStr,
                    "outputFile": outputFile,
                    "chunkSize": args.chunkSize # Store original target
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
                    sys.exit(1)

    console.print(f"[bold green]Done![/bold green] Total records this session: [yellow]{totalRecords}[/yellow]")

if __name__ == "__main__":
    runBatchQuery()
