#!/usr/bin/env python3
import pandas as pd
import os
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

def analyzeSensorQuality():
    files = [f for f in os.listdir('.') if f.startswith('chicago_temp_') and f.endswith('.csv')]
    
    if not files:
        console.print("[red]No Chicago data files found.[/red]")
        return

    table = Table(title="Chicago Sensor-Level Quality Audit")
    table.add_column("Node", style="cyan")
    table.add_column("Sensor", style="magenta")
    table.add_column("Host (Location)", style="green")
    table.add_column("Min (°F)", justify="right")
    table.add_column("Max (°F)", justify="right")
    table.add_column("Count", justify="right")
    table.add_column("Reliability", justify="center")

    for file in track(files, description="Auditing sensors..."):
        vsn = file.split('_')[-1].replace('.csv', '')
        try:
            # We process in chunks to handle the massive 12GB+ files
            chunk_size = 1000000
            # Track stats per (sensor, host) combination
            stats = {}

            for chunk in pd.read_csv(file, usecols=['value', 'meta.sensor', 'meta.host'], chunksize=chunk_size, low_memory=False, on_bad_lines='skip'):
                chunk['value'] = pd.to_numeric(chunk['value'], errors='coerce')
                chunk['value_f'] = (chunk['value'] * 9/5) + 32
                
                # Group by sensor and host
                groups = chunk.groupby(['meta.sensor', 'meta.host'])
                for (sensor, host), group in groups:
                    key = (sensor, host)
                    if key not in stats:
                        stats[key] = {'min': float('inf'), 'max': float('-inf'), 'count': 0, 'bad': 0}
                    
                    vals = group['value_f'].dropna()
                    if vals.empty: continue
                    
                    stats[key]['min'] = min(stats[key]['min'], vals.min())
                    stats[key]['max'] = max(stats[key]['max'], vals.max())
                    stats[key]['count'] += len(vals)
                    # Count "impossible" values as a proxy for failure
                    stats[key]['bad'] += len(vals[(vals < -45) | (vals > 120)])

            for (sensor, host), s in stats.items():
                reliability = "✅ GOOD"
                if s['bad'] > 0:
                    percent_bad = (s['bad'] / s['count']) * 100
                    reliability = f"⚠️ {percent_bad:.1f}% FAIL"
                if s['max'] > 115 and "core" in str(host):
                    reliability = "🔥 HEATED"
                
                table.add_row(
                    vsn,
                    str(sensor),
                    str(host).split('.')[0], # Simplify host name
                    f"{s['min']:.1f}",
                    f"{s['max']:.1f}",
                    f"{s['count']:,}",
                    reliability
                )

        except Exception as e:
            console.print(f"[red]Error analyzing {vsn}: {e}[/red]")

    console.print(table)

if __name__ == "__main__":
    analyzeSensorQuality()
