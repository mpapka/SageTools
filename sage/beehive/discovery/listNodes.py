#!/usr/bin/env python3
"""
Beehive Node Registry Scanner

Queries the Sage Beehive platform to discover all registered nodes,
their geographic locations, installation dates, last activity, and complete
activity history.

Features:
- Fetches comprehensive node metadata from Beehive API
- Recovers historical GPS coordinates for all nodes
- Maps complete activity periods with weekly granularity
- Displays results sorted by installation date (newest at bottom)
- Interactive CSV export with customizable filename
- Rich terminal output with colors and formatted tables
"""

import sage_data_client
import pandas as pd
import argparse
import json
import warnings
import os
import pickle
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Confirm, Prompt
from rich import box

# Initialize Rich console for colorful output
console = Console()

# Silence persistent pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

# Default checkpoint file for resumable operation
DEFAULT_CHECKPOINT_FILE = ".listNodes.checkpoint"


def loadCheckpoint(checkpointFile: str = None) -> dict:
    """
    Load checkpoint data if it exists.

    Args:
        checkpointFile: Path to checkpoint file (default: .listNodes.checkpoint)

    Returns:
        Checkpoint data containing nodes DataFrame and activity progress,
        or None if no checkpoint exists
    """
    checkpointFile = checkpointFile or DEFAULT_CHECKPOINT_FILE

    if os.path.exists(checkpointFile):
        try:
            with open(checkpointFile, 'rb') as f:
                checkpoint = pickle.load(f)
                console.print(f"[green]Found checkpoint from {checkpoint.get('timestamp', 'unknown time')}[/green]")
                return checkpoint
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load checkpoint: {e}[/yellow]")
            return None
    return None


def saveCheckpoint(nodes: pd.DataFrame, activityData: dict, currentStart: datetime, checkpointFile: str = None):
    """
    Save current progress to checkpoint file.

    Args:
        nodes: DataFrame containing node information
        activityData: Dictionary of activity periods per node
        currentStart: Current position in time series scanning
        checkpointFile: Path to checkpoint file
    """
    checkpointFile = checkpointFile or DEFAULT_CHECKPOINT_FILE

    try:
        checkpoint = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'nodes': nodes,
            'activityData': activityData,
            'currentStart': currentStart
        }
        with open(checkpointFile, 'wb') as f:
            pickle.dump(checkpoint, f)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save checkpoint: {e}[/yellow]")


def listAllNodes(reset: bool = False, outputFile: str = None, checkpointFile: str = None):
    """
    Main function to discover and list all Beehive nodes.

    This function performs the following operations:
    1. Queries Beehive API for first contact (birth) of each node
    2. Queries for last contact to determine current status
    3. Recovers historical GPS coordinates from sys.gps metrics
    4. Maps complete activity history with weekly granularity
    5. Displays formatted results in a rich table
    6. Optionally exports data to CSV file

    Args:
        reset: If True, ignore any existing checkpoint and start fresh
        outputFile: Output CSV filename (default: nodeRegistry.csv)
        checkpointFile: Checkpoint file path

    Returns:
        DataFrame with node data, or None on error
    """
    checkpointFile = checkpointFile or DEFAULT_CHECKPOINT_FILE

    # Display welcome header
    console.print(Panel.fit(
        "[bold cyan]Beehive Node Registry Scanner[/bold cyan]\n"
        "[dim]Discovering all nodes in the Sage network...[/dim]",
        border_style="cyan"
    ))

    # Check for existing checkpoint
    checkpoint = None if reset else loadCheckpoint(checkpointFile)
    if checkpoint and not reset:
        resume = Confirm.ask(
            "[bold cyan]Resume from checkpoint?[/bold cyan]",
            default=True
        )
        if not resume:
            checkpoint = None
            if os.path.exists(checkpointFile):
                os.remove(checkpointFile)

    try:
        # If resuming from checkpoint, skip initial data gathering
        if checkpoint:
            nodes = checkpoint['nodes']
            activityData = checkpoint['activityData']
            currentStart = checkpoint['currentStart']
            console.print(f"[green]Resuming from {currentStart.strftime('%Y-%m-%d')}[/green]")
        else:
            # Step 1: Get the first ever record for each node to determine "Birth"
            console.print("\n[yellow]>[/yellow] [bold]Searching for first contact (Birth) for all nodes...[/bold]")
            birthDf = sage_data_client.query(
                start="2018-01-01T00:00:00Z",
                head=1,
                filter={"name": "sys.uptime"}
            )

            # Step 2: Get the last ever record for each node to determine "Last Seen"
            console.print("[yellow]>[/yellow] [bold]Searching for last contact (End of Life) for all nodes...[/bold]")
            deathDf = sage_data_client.query(
                start="2018-01-01T00:00:00Z",
                tail=1,
                filter={"name": "sys.uptime"}
            )

            # Validate we got data
            if birthDf.empty or deathDf.empty:
                console.print("[red]No node data found.[/red]", style="bold red")
                return None

            # Step 3: Prepare base node information
            availableCols = birthDf.columns.tolist()
            neededCols = ['meta.vsn', 'timestamp']
            if 'meta.lat' in availableCols:
                neededCols.append('meta.lat')
            if 'meta.lon' in availableCols:
                neededCols.append('meta.lon')

            birthInfo = birthDf[neededCols].copy()

            # Rename columns for clarity
            renameMap = {'meta.vsn': 'vsn', 'timestamp': 'firstSeen'}
            if 'meta.lat' in availableCols:
                renameMap['meta.lat'] = 'lat'
            if 'meta.lon' in availableCols:
                renameMap['meta.lon'] = 'lon'
            birthInfo.columns = [renameMap.get(c, c) for c in birthInfo.columns]
            birthInfo = birthInfo.sort_values('firstSeen').drop_duplicates('vsn')

            # Ensure lat/lon columns exist (even if empty)
            if 'lat' not in birthInfo.columns:
                birthInfo['lat'] = None
            if 'lon' not in birthInfo.columns:
                birthInfo['lon'] = None

            # Process "last seen" data
            deathInfo = deathDf[['meta.vsn', 'timestamp']].copy()
            deathInfo.columns = ['vsn', 'lastSeen']
            deathInfo = deathInfo.sort_values('lastSeen', ascending=False).drop_duplicates('vsn')

            # Ensure VSN is string type for proper merging
            birthInfo['vsn'] = birthInfo['vsn'].astype(str)
            deathInfo['vsn'] = deathInfo['vsn'].astype(str)

            # Step 4: Merge birth and death data, then clean
            nodes = pd.merge(birthInfo, deathInfo, on='vsn')
            nodes = nodes[nodes['vsn'].astype(str).str.lower() != 'nan']
            nodes['firstSeen'] = pd.to_datetime(nodes['firstSeen'])
            nodes['lastSeen'] = pd.to_datetime(nodes['lastSeen'])

            # Remove invalid entries where last seen is before first seen
            nodes = nodes[nodes['lastSeen'] >= nodes['firstSeen']]

            # Step 5: Recover ALL historical GPS locations
            console.print("[yellow]>[/yellow] [bold]Recovering historical locations from sys.gps metrics...[/bold]")
            try:
                # Query the entire history but only take the latest 1 record per node
                allGpsLat = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    filter={"name": "sys.gps.lat"},
                    tail=1
                )
                allGpsLon = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    filter={"name": "sys.gps.lon"},
                    tail=1
                )

                # Fill in missing coordinates with GPS data
                if not allGpsLat.empty:
                    latMap = dict(zip(allGpsLat['meta.vsn'].astype(str), allGpsLat['value']))
                    nodes['lat'] = nodes['lat'].fillna(nodes['vsn'].map(latMap))
                if not allGpsLon.empty:
                    lonMap = dict(zip(allGpsLon['meta.vsn'].astype(str), allGpsLon['value']))
                    nodes['lon'] = nodes['lon'].fillna(nodes['vsn'].map(lonMap))

                console.print("  [green]GPS data recovered successfully[/green]")
            except Exception as gpsErr:
                console.print(f"  [yellow]Warning: GPS recovery failed: {gpsErr}[/yellow]")

            # Initialize activity tracking
            activityData = {vsn: [] for vsn in nodes['vsn']}
            currentStart = nodes['firstSeen'].min()

        # Step 6: Capture Active Periods (weekly granularity)
        console.print("[yellow]>[/yellow] [bold]Mapping active periods (weekly granularity)...[/bold]")
        binDelta = timedelta(weeks=1)
        globalStart = nodes['firstSeen'].min()
        globalEnd = nodes['lastSeen'].max()

        # Calculate total weeks and current position
        totalWeeks = int((globalEnd - globalStart).total_seconds() / binDelta.total_seconds())
        weeksCompleted = int((currentStart - globalStart).total_seconds() / binDelta.total_seconds()) if checkpoint else 0

        console.print(f"[dim]Total time span: {globalStart.strftime('%Y-%m-%d')} to {globalEnd.strftime('%Y-%m-%d')}[/dim]")
        console.print(f"[dim]Total weeks to scan: {totalWeeks:,}[/dim]")
        if checkpoint:
            console.print(f"[dim]Already completed: {weeksCompleted:,} weeks[/dim]")

        # Progress bar for activity mapping with detailed feedback
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("|"),
            TextColumn("[cyan]{task.fields[weekInfo]}[/cyan]"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Scanning activity...",
                total=totalWeeks,
                completed=weeksCompleted,
                weekInfo=f"Week {weeksCompleted}/{totalWeeks}"
            )

            weekCount = weeksCompleted
            checkpointInterval = 50  # Save checkpoint every 50 weeks

            while currentStart < globalEnd:
                currentEnd = currentStart + binDelta
                try:
                    # Query for any uptime data in this time window
                    activeInWindow = sage_data_client.query(
                        start=currentStart.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        end=currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        filter={"name": "sys.uptime"},
                        tail=1
                    )

                    if not activeInWindow.empty:
                        seenVsns = set(activeInWindow['meta.vsn'].unique().astype(str))
                        for vsn in seenVsns:
                            if vsn in activityData:
                                # Merge adjacent active weeks into single tuples
                                if (activityData[vsn] and
                                    activityData[vsn][-1][1] == currentStart.isoformat()):
                                    activityData[vsn][-1] = (
                                        activityData[vsn][-1][0],
                                        currentEnd.isoformat()
                                    )
                                else:
                                    activityData[vsn].append((
                                        currentStart.isoformat(),
                                        currentEnd.isoformat()
                                    ))
                except Exception:
                    pass

                currentStart = currentEnd
                weekCount += 1

                # Update progress with detailed info
                progress.update(
                    task,
                    advance=1,
                    weekInfo=f"Week {weekCount:,}/{totalWeeks:,} ({currentStart.strftime('%Y-%m-%d')})"
                )

                # Save checkpoint periodically
                if weekCount % checkpointInterval == 0:
                    saveCheckpoint(nodes, activityData, currentStart, checkpointFile)

        # Add activity periods to dataframe
        nodes['activePeriods'] = nodes['vsn'].map(
            lambda x: json.dumps(activityData.get(x, []))
        )

        # Clean up checkpoint file on successful completion
        if os.path.exists(checkpointFile):
            os.remove(checkpointFile)
            console.print("[green]Scan complete - checkpoint cleared[/green]")

        # Step 7: Sort by installation date (firstSeen) - newest at bottom
        nodes = nodes.sort_values('firstSeen', ascending=True)

        # Step 8: Display results in a beautiful table
        console.print("\n")
        table = Table(
            title="[bold cyan]Beehive Node Registry[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan"
        )

        table.add_column("VSN", style="cyan", no_wrap=True)
        table.add_column("Latitude", style="green")
        table.add_column("Longitude", style="green")
        table.add_column("First Seen", style="yellow")
        table.add_column("Last Seen", style="blue")
        table.add_column("Activity Blocks", style="red", justify="right")

        for _, row in nodes.iterrows():
            lat = f"{row['lat']:.4f}" if pd.notnull(row['lat']) else "N/A"
            lon = f"{row['lon']:.4f}" if pd.notnull(row['lon']) else "N/A"
            periods = json.loads(row['activePeriods'])
            firstSeen = str(row['firstSeen'])[:19]
            lastSeen = str(row['lastSeen'])[:19]

            table.add_row(
                row['vsn'],
                lat,
                lon,
                firstSeen,
                lastSeen,
                str(len(periods))
            )

        console.print(table)

        # Display summary statistics
        console.print(Panel.fit(
            f"[bold green]Total valid nodes found: {len(nodes)}[/bold green]",
            border_style="green"
        ))

        # Step 9: Prompt user for CSV export
        console.print("\n")
        shouldExport = Confirm.ask(
            "[bold cyan]Would you like to export this data to a CSV file?[/bold cyan]",
            default=True
        )

        if shouldExport:
            defaultFilename = outputFile or "nodeRegistry.csv"
            customFilename = Prompt.ask(
                f"[bold cyan]Enter filename[/bold cyan] [dim](press Enter for '{defaultFilename}')[/dim]",
                default=defaultFilename
            )

            # Ensure .csv extension
            if not customFilename.endswith('.csv'):
                customFilename += '.csv'

            # Export to CSV
            nodes.to_csv(customFilename, index=False)
            console.print(f"[green]Registry saved to [bold green]{customFilename}[/bold green][/green]")
        else:
            console.print("[dim]Export skipped.[/dim]")

        return nodes

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]Error retrieving node registry: {e}[/red]", style="bold red")
        return None


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(
        description="Discover and list all Beehive nodes with resumable scanning"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Ignore checkpoint and start fresh scan'
    )
    parser.add_argument(
        '--output',
        help='Output CSV filename (default: nodeRegistry.csv)'
    )
    args = parser.parse_args()

    listAllNodes(reset=args.reset, outputFile=args.output)


if __name__ == "__main__":
    main()
