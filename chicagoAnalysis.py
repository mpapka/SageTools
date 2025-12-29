#!/usr/bin/env python3
import pandas as pd
import os
import json
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

def runAnalysis():
    files = [f for f in os.listdir('.') if f.startswith('chicago_temp_') and f.endswith('.csv')]
    
    if not files:
        console.print("[red]No Chicago data files found.[/red]")
        return

    table = Table(title="Chicago City-Wide Climate Analysis")
    table.add_column("Node (VSN)", style="cyan")
    table.add_column("Min Temp (°F)", justify="right", style="bold blue")
    table.add_column("Max Temp (°F)", justify="right", style="bold red")
    table.add_column("Avg Temp (°F)", justify="right")
    table.add_column("Sensors", style="magenta")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Status", justify="center")

    results = []

    for file in track(files, description="Analyzing datasets..."):
        vsn = file.split('_')[-1].replace('.csv', '')
        
        try:
            # We process in chunks to handle the massive 12GB+ files safely
            min_val = float('inf')
            max_val = float('-inf')
            total_sum = 0
            total_count = 0
            sensors = set()
            
            # Read 'value' and 'meta.sensor' columns
            chunk_size = 1000000
            for chunk in pd.read_csv(file, usecols=['value', 'meta.sensor'], chunksize=chunk_size, low_memory=False, on_bad_lines='skip'):
                vals = pd.to_numeric(chunk['value'], errors='coerce').dropna()
                if vals.empty: continue
                
                if 'meta.sensor' in chunk.columns:
                    sensors.update(chunk['meta.sensor'].dropna().unique())
                
                # Convert to Fahrenheit immediately
                f_vals = (vals * 9/5) + 32
                
                min_val = min(min_val, f_vals.min())
                max_val = max(max_val, f_vals.max())
                total_sum += f_vals.sum()
                total_count += len(f_vals)

            sensor_str = ", ".join(sorted(list(sensors)))
            if total_count > 0:
                avg_val = total_sum / total_count
                table.add_row(
                    vsn, 
                    f"{min_val:.1f}°F", 
                    f"{max_val:.1f}°F", 
                    f"{avg_val:.1f}°F",
                    sensor_str,
                    f"{total_count:,}",
                    "[green]COMPLETE[/green]"
                )
            else:
                table.add_row(vsn, "-", "-", "-", "0", "[yellow]EMPTY[/yellow]")

        except Exception as e:
            table.add_row(vsn, "ERR", "ERR", "ERR", "-", f"[red]{str(e)[:20]}[/red]")

    console.print("\n")
    console.print(table)
    console.print("\n[bold yellow]Analysis Complete.[/bold yellow] Use [bold cyan]plotChicagoComparison.py[/bold cyan] to visualize these trends.")

if __name__ == "__main__":
    runAnalysis()
