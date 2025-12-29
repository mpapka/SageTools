#!/usr/bin/env python3
import pandas as pd
import os
import argparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel

console = Console()

def fixCsv(inputFile, progress, mainTask):
    if not os.path.exists(inputFile):
        console.print(f"[red]Error: {inputFile} not found.[/red]")
        return False

    outputFile = inputFile.replace(".csv", "_fixed.csv")
    
    # We'll use row-based progress estimation
    # First, quickly count lines or estimate based on file size
    fileSize = os.path.getsize(inputFile)
    # Average Beehive row is roughly 250 bytes
    estimatedRows = fileSize // 250
    
    scanTask = progress.add_task(f"  [cyan]Scanning {os.path.basename(inputFile)}", total=estimatedRows)
    all_columns = set()
    chunk_size = 500000 
    
    try:
        # Phase 1: Column Discovery
        total_rows = 0
        for chunk in pd.read_csv(inputFile, chunksize=chunk_size, low_memory=False, on_bad_lines='skip'):
            all_columns.update(chunk.columns)
            total_rows += len(chunk)
            progress.update(scanTask, completed=total_rows)
        
        # Now we know exact row count
        progress.update(scanTask, total=total_rows, completed=total_rows)
        col_list = sorted(list(all_columns))
        
        # Phase 2: Rewrite
        if os.path.exists(outputFile):
            os.remove(outputFile)
            
        writeTask = progress.add_task(f"  [green]Standardizing {os.path.basename(inputFile)}", total=total_rows)
        first_chunk = True
        processed_rows = 0
        
        for chunk in pd.read_csv(inputFile, chunksize=chunk_size, low_memory=False, on_bad_lines='skip'):
            chunk = chunk.reindex(columns=col_list)
            chunk.to_csv(outputFile, mode='a', index=False, header=first_chunk)
            first_chunk = False
            processed_rows += len(chunk)
            progress.update(writeTask, completed=processed_rows)
            
        progress.remove_task(scanTask)
        progress.remove_task(writeTask)
        return True

    except Exception as e:
        console.print(f"[red]Failed to fix {inputFile}: {e}[/red]")
        return False

def runBatchFix(files):
    console.print(Panel("[bold cyan]Beehive CSV Format Standardizer[/bold cyan]\nUnifying metadata columns across all chunks.", expand=False))
    
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
        
        for file in files:
            success = fixCsv(file, progress, mainTask)
            if success:
                progress.advance(mainTask)
                
    console.print("\n[bold green]All files processed successfully![/bold green]")
    console.print("You can now rename the [cyan]_fixed.csv[/cyan] files to their original names.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standardize CSV column structure for mixed-format Beehive data.")
    parser.add_argument("files", nargs="+", help="The CSV file(s) to fix")
    args = parser.parse_args()
    
    # Expand globs if shell doesn't do it
    import glob
    expanded_files = []
    for f in args.files:
        expanded_files.extend(glob.glob(f))
    
    if not expanded_files:
        console.print("[red]No matching files found.[/red]")
    else:
        runBatchFix(expanded_files)
