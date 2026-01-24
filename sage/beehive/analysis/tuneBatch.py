#!/usr/bin/env python3
"""
Batch tuning benchmark for Beehive queries.

Tests different time window sizes to determine optimal chunk size
for batch data extraction.
"""

import sage_data_client
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table

console = Console()


def benchmark(
    vsn: str = "W01B",
    metric: str = "env.temperature",
    baseStart: datetime = None
) -> Optional[Dict]:
    """
    Run batch tuning benchmark.

    Tests various time window sizes to find optimal throughput.

    Args:
        vsn: Node VSN to test
        metric: Metric to query
        baseStart: Start date for testing (default: 2023-06-01)

    Returns:
        Dictionary with benchmark results and recommendation
    """
    if baseStart is None:
        baseStart = datetime(2023, 6, 1)

    # Test windows: 1 hour, 6 hours, 12 hours, 1 day, 2 days, 4 days, 7 days
    testWindows = [
        ("1h", timedelta(hours=1)),
        ("6h", timedelta(hours=6)),
        ("12h", timedelta(hours=12)),
        ("1d", timedelta(days=1)),
        ("2d", timedelta(days=2)),
        ("4d", timedelta(days=4)),
        ("7d", timedelta(days=7))
    ]

    results = []

    table = Table(title=f"Beehive Batch Tuning Benchmark (Node: {vsn})")
    table.add_column("Window", style="cyan")
    table.add_column("Rows", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("Rows/Sec", justify="right", style="green")
    table.add_column("Status", justify="center")

    console.print(f"Starting benchmark for [bold]{vsn}[/bold]...")

    for label, delta in testWindows:
        startStr = baseStart.strftime('%Y-%m-%dT%H:%M:%SZ')
        endStr = (baseStart + delta).strftime('%Y-%m-%dT%H:%M:%SZ')

        startTime = time.time()
        try:
            df = sage_data_client.query(
                start=startStr,
                end=endStr,
                filter={"name": metric, "vsn": vsn}
            )
            elapsed = time.time() - startTime

            numRows = len(df)
            rowsPerSec = int(numRows / elapsed) if elapsed > 0 else 0

            table.add_row(label, str(numRows), f"{elapsed:.2f}", str(rowsPerSec), "[green]SUCCESS[/green]")
            results.append({"label": label, "rows": numRows, "elapsed": elapsed, "rps": rowsPerSec, "success": True})

        except Exception as e:
            elapsed = time.time() - startTime
            status = "500 ERROR" if "500" in str(e) else "FAILED"
            table.add_row(label, "-", f"{elapsed:.2f}", "-", f"[red]{status}[/red]")
            results.append({"label": label, "success": False, "error": str(e)})

    console.print(table)

    # Recommendation
    successful = [r for r in results if r['success']]
    recommendation = None

    if successful:
        best = max(successful, key=lambda x: x['rps'])
        recommendation = best['label']
        console.print(f"\n[bold yellow]Recommendation:[/bold yellow] Use [bold cyan]{recommendation}[/bold cyan] chunks for maximum throughput.")
    else:
        console.print("\n[bold red]All tests failed.[/bold red] Try even smaller chunks (e.g., 30m).")

    return {
        "vsn": vsn,
        "metric": metric,
        "results": results,
        "recommendation": recommendation
    }


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Benchmark batch query performance")
    parser.add_argument("--vsn", default="W01B", help="Node VSN to test")
    parser.add_argument("--metric", default="env.temperature", help="Metric to query")
    parser.add_argument("--start", help="Start date for testing (YYYY-MM-DD)")
    args = parser.parse_args()

    baseStart = None
    if args.start:
        from dateutil.parser import parse as parseDate
        baseStart = parseDate(args.start)

    benchmark(args.vsn, args.metric, baseStart)


if __name__ == "__main__":
    main()
