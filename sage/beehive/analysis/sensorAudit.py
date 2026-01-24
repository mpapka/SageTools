#!/usr/bin/env python3
"""
Sensor quality auditing for Beehive temperature data.

Analyzes sensor-level data quality, identifying potential hardware failures
and internal heating biases.
"""

import pandas as pd
import os
import argparse
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


def auditFile(filepath: str, chunkSize: int = 1000000) -> List[Dict]:
    """
    Audit sensor quality for a single CSV file.

    Args:
        filepath: Path to CSV file
        chunkSize: Number of rows to process at a time

    Returns:
        List of sensor audit results
    """
    if not os.path.exists(filepath):
        return []

    vsn = os.path.basename(filepath).split('_')[-1].replace('.csv', '')

    try:
        # Track stats per (sensor, host) combination
        stats = {}

        for chunk in pd.read_csv(filepath, usecols=['value', 'meta.sensor', 'meta.host'],
                                  chunksize=chunkSize, low_memory=False, on_bad_lines='skip'):
            chunk['value'] = pd.to_numeric(chunk['value'], errors='coerce')
            chunk['valueF'] = (chunk['value'] * 9/5) + 32

            # Group by sensor and host
            groups = chunk.groupby(['meta.sensor', 'meta.host'])
            for (sensor, host), group in groups:
                key = (sensor, host)
                if key not in stats:
                    stats[key] = {'min': float('inf'), 'max': float('-inf'), 'count': 0, 'bad': 0}

                vals = group['valueF'].dropna()
                if vals.empty:
                    continue

                stats[key]['min'] = min(stats[key]['min'], vals.min())
                stats[key]['max'] = max(stats[key]['max'], vals.max())
                stats[key]['count'] += len(vals)
                # Count "impossible" values as a proxy for failure
                stats[key]['bad'] += len(vals[(vals < -45) | (vals > 120)])

        results = []
        for (sensor, host), s in stats.items():
            reliability = "GOOD"
            if s['bad'] > 0:
                percentBad = (s['bad'] / s['count']) * 100
                reliability = f"{percentBad:.1f}% FAIL"
            if s['max'] > 115 and "core" in str(host):
                reliability = "HEATED"

            results.append({
                'vsn': vsn,
                'sensor': str(sensor),
                'host': str(host).split('.')[0],
                'minF': s['min'],
                'maxF': s['max'],
                'count': s['count'],
                'reliability': reliability
            })

        return results

    except Exception as e:
        console.print(f"[red]Error analyzing {vsn}: {e}[/red]")
        return []


def analyzeSensorQuality(pattern: str = "chicago_temp_*.csv", directory: str = ".") -> List[Dict]:
    """
    Audit sensor quality across multiple files.

    Args:
        pattern: Glob pattern for matching files
        directory: Directory to search

    Returns:
        List of all sensor audit results
    """
    import glob

    files = glob.glob(os.path.join(directory, pattern))

    if not files:
        console.print("[red]No matching data files found.[/red]")
        return []

    table = Table(title="Sensor-Level Quality Audit")
    table.add_column("Node", style="cyan")
    table.add_column("Sensor", style="magenta")
    table.add_column("Host (Location)", style="green")
    table.add_column("Min (F)", justify="right")
    table.add_column("Max (F)", justify="right")
    table.add_column("Count", justify="right")
    table.add_column("Reliability", justify="center")

    allResults = []

    for filepath in track(files, description="Auditing sensors..."):
        results = auditFile(filepath)
        allResults.extend(results)

        for r in results:
            reliabilityStyle = {
                'GOOD': '[green]GOOD[/green]',
                'HEATED': '[red]HEATED[/red]'
            }.get(r['reliability'], f"[yellow]{r['reliability']}[/yellow]")

            table.add_row(
                r['vsn'],
                r['sensor'],
                r['host'],
                f"{r['minF']:.1f}",
                f"{r['maxF']:.1f}",
                f"{r['count']:,}",
                reliabilityStyle
            )

    console.print(table)

    return allResults


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Audit sensor quality in Beehive data files")
    parser.add_argument("--pattern", default="chicago_temp_*.csv", help="File pattern to match")
    parser.add_argument("--directory", default=".", help="Directory to search")
    args = parser.parse_args()

    analyzeSensorQuality(args.pattern, args.directory)


if __name__ == "__main__":
    main()
