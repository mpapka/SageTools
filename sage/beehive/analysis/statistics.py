#!/usr/bin/env python3
"""
Climate statistics and analysis for Beehive temperature data.

Provides functions for analyzing temperature data files and generating
summary statistics.
"""

import pandas as pd
import os
import argparse
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


def analyzeFile(filepath: str, chunkSize: int = 1000000) -> Optional[Dict]:
    """
    Analyze a single temperature CSV file.

    Args:
        filepath: Path to CSV file
        chunkSize: Number of rows to process at a time

    Returns:
        Dictionary with statistics, or None on error
    """
    if not os.path.exists(filepath):
        return None

    vsn = os.path.basename(filepath).split('_')[-1].replace('.csv', '')

    try:
        minVal = float('inf')
        maxVal = float('-inf')
        totalSum = 0
        totalCount = 0
        sensors = set()

        for chunk in pd.read_csv(filepath, usecols=['value', 'meta.sensor'],
                                  chunksize=chunkSize, low_memory=False, on_bad_lines='skip'):
            vals = pd.to_numeric(chunk['value'], errors='coerce').dropna()
            if vals.empty:
                continue

            if 'meta.sensor' in chunk.columns:
                sensors.update(chunk['meta.sensor'].dropna().unique())

            # Convert to Fahrenheit
            fVals = (vals * 9/5) + 32

            minVal = min(minVal, fVals.min())
            maxVal = max(maxVal, fVals.max())
            totalSum += fVals.sum()
            totalCount += len(fVals)

        if totalCount == 0:
            return {
                'vsn': vsn,
                'minF': None,
                'maxF': None,
                'avgF': None,
                'sensors': [],
                'count': 0,
                'status': 'EMPTY'
            }

        return {
            'vsn': vsn,
            'minF': minVal,
            'maxF': maxVal,
            'avgF': totalSum / totalCount,
            'sensors': sorted(list(sensors)),
            'count': totalCount,
            'status': 'COMPLETE'
        }

    except Exception as e:
        return {
            'vsn': vsn,
            'minF': None,
            'maxF': None,
            'avgF': None,
            'sensors': [],
            'count': 0,
            'status': f'ERROR: {str(e)[:20]}'
        }


def runAnalysis(pattern: str = "chicago_temp_*.csv", directory: str = ".") -> List[Dict]:
    """
    Analyze multiple temperature CSV files.

    Args:
        pattern: Glob pattern for matching files
        directory: Directory to search in

    Returns:
        List of analysis results
    """
    import glob

    files = glob.glob(os.path.join(directory, pattern))

    if not files:
        console.print("[red]No matching data files found.[/red]")
        return []

    table = Table(title="Climate Analysis")
    table.add_column("Node (VSN)", style="cyan")
    table.add_column("Min Temp (F)", justify="right", style="bold blue")
    table.add_column("Max Temp (F)", justify="right", style="bold red")
    table.add_column("Avg Temp (F)", justify="right")
    table.add_column("Sensors", style="magenta")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Status", justify="center")

    results = []

    for filepath in track(files, description="Analyzing datasets..."):
        result = analyzeFile(filepath)
        if result:
            results.append(result)

            statusStyle = {
                'COMPLETE': '[green]COMPLETE[/green]',
                'EMPTY': '[yellow]EMPTY[/yellow]'
            }.get(result['status'], f"[red]{result['status']}[/red]")

            if result['count'] > 0:
                table.add_row(
                    result['vsn'],
                    f"{result['minF']:.1f}F",
                    f"{result['maxF']:.1f}F",
                    f"{result['avgF']:.1f}F",
                    ", ".join(result['sensors']),
                    f"{result['count']:,}",
                    statusStyle
                )
            else:
                table.add_row(
                    result['vsn'],
                    "-", "-", "-",
                    "-", "0",
                    statusStyle
                )

    console.print("\n")
    console.print(table)
    console.print("\n[bold yellow]Analysis Complete.[/bold yellow]")

    return results


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Analyze Beehive temperature data files")
    parser.add_argument("--pattern", default="chicago_temp_*.csv", help="File pattern to match")
    parser.add_argument("--directory", default=".", help="Directory to search")
    args = parser.parse_args()

    runAnalysis(args.pattern, args.directory)


if __name__ == "__main__":
    main()
