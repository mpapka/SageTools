#!/usr/bin/env python3
import sage_data_client
import time
import pandas as pd
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

console = Console()

def benchmark():
    vsn = "W01B"  # Large dataset node
    metric = "env.temperature"
    
    # Test windows: 1 hour, 6 hours, 12 hours, 1 day, 2 days, 4 days
    testWindows = [
        ("1h", timedelta(hours=1)),
        ("6h", timedelta(hours=6)),
        ("12h", timedelta(hours=12)),
        ("1d", timedelta(days=1)),
        ("2d", timedelta(days=2)),
        ("4d", timedelta(days=4)),
        ("7d", timedelta(days=7))
    ]
    
    # We use a fixed recent start time to ensure data exists
    # but not too recent to avoid "live" data edge cases
    baseStart = datetime(2023, 6, 1)
    
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
            results.append({"label": label, "rps": rowsPerSec, "success": True})
            
        except Exception as e:
            elapsed = time.time() - startTime
            status = "500 ERROR" if "500" in str(e) else "FAILED"
            table.add_row(label, "-", f"{elapsed:.2f}", "-", f"[red]{status}[/red]")
            results.append({"label": label, "success": False})

    console.print(table)
    
    # Recommendation
    successful = [r for r in results if r['success']]
    if successful:
        best = max(successful, key=lambda x: x['rps'])
        console.print(f"\n[bold yellow]Recommendation:[/bold yellow] Use [bold cyan]{best['label']}[/bold cyan] chunks for maximum throughput.")
    else:
        console.print("\n[bold red]All tests failed.[/bold red] Try even smaller chunks (e.g. 30m).")

if __name__ == "__main__":
    benchmark()
