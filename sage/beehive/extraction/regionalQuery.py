#!/usr/bin/env python3
"""
BeeHive Pro - Region-based multi-node data extraction.

Provides advanced functionality for extracting data from all nodes
within a geographic region.
"""

import sage_data_client
import pandas as pd
import argparse
import os
import json
import sys
import time
import warnings
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parseDate
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel

from ...common.regions import RegionManager
from ...common.csvUtils import alignColumns, getExistingColumns

# Configuration
console = Console()
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)


class BeeHivePro:
    """
    Advanced Beehive data extraction with region support.

    Provides functionality to:
    - Sync global node registry with GPS coordinates
    - Filter nodes by geographic region
    - Batch extract data from multiple nodes
    """

    def __init__(self, registryFile: str = "nodeRegistry.csv"):
        """
        Initialize BeeHivePro.

        Args:
            registryFile: Path to node registry CSV file
        """
        self.registryFile = registryFile
        self.registry = None
        self.regions = RegionManager()

    def loadRegistry(self, forceUpdate: bool = False) -> pd.DataFrame:
        """
        Load or sync the node registry.

        Args:
            forceUpdate: If True, always sync from API

        Returns:
            DataFrame with node information
        """
        if not os.path.exists(self.registryFile) or forceUpdate:
            self.syncRegistry()

        self.registry = pd.read_csv(self.registryFile)
        self.registry['vsn'] = self.registry['vsn'].astype(str)
        return self.registry

    def syncRegistry(self) -> bool:
        """
        Sync global node registry from Beehive API.

        Returns:
            True on success
        """
        try:
            with console.status("[bold green]Syncing Global Node Registry (including GPS)...") as status:
                birthDf = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    head=1,
                    filter={"name": "sys.uptime"}
                )
                deathDf = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    tail=1,
                    filter={"name": "sys.uptime"}
                )
                gpsLat = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    filter={"name": "sys.gps.lat"},
                    tail=1
                )
                gpsLon = sage_data_client.query(
                    start="2018-01-01T00:00:00Z",
                    filter={"name": "sys.gps.lon"},
                    tail=1
                )

                birthInfo = birthDf[['meta.vsn', 'timestamp', 'meta.lat', 'meta.lon']].copy()
                birthInfo.columns = ['vsn', 'firstSeen', 'lat', 'lon']
                deathInfo = deathDf[['meta.vsn', 'timestamp']].copy()
                deathInfo.columns = ['vsn', 'lastSeen']

                nodes = pd.merge(birthInfo, deathInfo, on='vsn').drop_duplicates('vsn')
                nodes = nodes[nodes['vsn'].astype(str).str.lower() != 'nan']

                if not gpsLat.empty:
                    latMap = dict(zip(gpsLat['meta.vsn'].astype(str), gpsLat['value']))
                    nodes['lat'] = nodes['lat'].fillna(nodes['vsn'].map(latMap))
                if not gpsLon.empty:
                    lonMap = dict(zip(gpsLon['meta.vsn'].astype(str), gpsLon['value']))
                    nodes['lon'] = nodes['lon'].fillna(nodes['vsn'].map(lonMap))

                nodes.to_csv(self.registryFile, index=False)
                console.print(f"[green]Successfully synced {len(nodes)} nodes to {self.registryFile}[/green]")
                return True

        except Exception as e:
            console.print(f"[red]Sync failed: {e}[/red]")
            return False

    def getNodesInRegion(self, regionQuery: str) -> pd.DataFrame:
        """
        Get all nodes within a geographic region.

        Args:
            regionQuery: Region name (e.g., "Chicago", "Illinois")
                        Can be prefixed with "outside " for inverse matching.

        Returns:
            DataFrame with matching nodes
        """
        self.loadRegistry()

        isOutside = False
        if regionQuery.lower().startswith("outside "):
            isOutside = True
            regionQuery = regionQuery[8:]

        bbox = self.regions.getBbox(regionQuery)
        if not bbox:
            return pd.DataFrame()

        mask = (
            (self.registry['lat'] >= bbox['lat'][0]) &
            (self.registry['lat'] <= bbox['lat'][1]) &
            (self.registry['lon'] >= bbox['lon'][0]) &
            (self.registry['lon'] <= bbox['lon'][1])
        )

        if isOutside:
            return self.registry[~mask & self.registry['lat'].notnull()]
        return self.registry[mask]

    def listNodesInRegion(self, regionQuery: str) -> List[str]:
        """
        List VSNs of all nodes in a region.

        Args:
            regionQuery: Region name

        Returns:
            List of VSN strings
        """
        nodes = self.getNodesInRegion(regionQuery)
        return nodes['vsn'].tolist() if not nodes.empty else []

    def fetch(
        self,
        vsn: str,
        metric: str,
        startStr: str,
        endStr: str = "now",
        targetChunkStr: str = "7d",
        output: str = None
    ) -> Optional[str]:
        """
        Fetch data for a single node with resume support.

        Args:
            vsn: Node VSN
            metric: Metric name
            startStr: Start time (or "all" for full history)
            endStr: End time
            targetChunkStr: Chunk size
            output: Output filename

        Returns:
            Output filename on success
        """
        self.loadRegistry()

        # Parse end time
        endTime = datetime.now(timezone.utc) if endStr == "now" else parseDate(endStr).replace(tzinfo=timezone.utc)

        # Handle "all" start time
        if startStr == "all":
            nodeInfo = self.registry[self.registry['vsn'] == vsn]
            if nodeInfo.empty:
                console.print(f"[red]Node {vsn} not found in registry[/red]")
                return None
            startTime = pd.to_datetime(nodeInfo['firstSeen'].iloc[0]).to_pydatetime()
            if startTime.tzinfo is None:
                startTime = startTime.replace(tzinfo=timezone.utc)
        elif startStr.startswith("-"):
            days = int(startStr[1:-1])
            startTime = endTime - timedelta(days=days)
        else:
            startTime = parseDate(startStr).replace(tzinfo=timezone.utc)

        # Generate output filename
        metricSafe = metric.replace('.', '').title().replace(' ', '')
        metricSafe = metricSafe[0].lower() + metricSafe[1:]
        outputFile = output if output else f"{metricSafe}{vsn}Pro.csv"
        checkpointPath = f".{outputFile}.checkpoint"

        # Check for existing checkpoint
        if os.path.exists(checkpointPath):
            with open(checkpointPath, 'r') as f:
                startTime = parseDate(json.load(f)['lastProcessedTimestamp']).replace(tzinfo=timezone.utc)

        # Parse chunk duration
        unit = targetChunkStr[-1]
        targetDuration = timedelta(days=int(targetChunkStr[:-1])) if unit == 'd' else timedelta(hours=int(targetChunkStr[:-1]))
        currentDuration = targetDuration
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
            console=console
        ) as progress:
            mainTask = progress.add_task(f"Fetching {vsn}", total=(endTime - startTime).total_seconds())

            while currentStart < endTime:
                currentEnd = min(currentStart + currentDuration, endTime)
                startIso = currentStart.strftime('%Y-%m-%dT%H:%M:%SZ')
                endIso = currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ')

                try:
                    durDays = currentDuration.total_seconds() / 86400
                    progress.update(mainTask, description=f"Node {vsn} ({durDays:.1f}d chunk)")

                    df = sage_data_client.query(
                        start=startIso,
                        end=endIso,
                        filter={"name": metric, "vsn": vsn}
                    )

                    if not df.empty:
                        existingCols = getExistingColumns(outputFile)
                        if existingCols and not writeHeader:
                            df = alignColumns(df, existingCols)
                        df.to_csv(outputFile, mode='a', index=False, header=writeHeader)
                        writeHeader = False
                        totalRecords += len(df)

                    with open(checkpointPath, 'w') as f:
                        json.dump({"lastProcessedTimestamp": endIso}, f)

                    progress.advance(mainTask, (currentEnd - currentStart).total_seconds())
                    currentStart = currentEnd
                    currentDuration = min(currentDuration * 2, targetDuration)

                except Exception as e:
                    if "500" in str(e):
                        currentDuration = max(currentDuration / 2, timedelta(hours=1))
                        time.sleep(1)
                    else:
                        console.print(f"[red]Error: {e}[/red]")
                        return None

        # Clear checkpoint
        if os.path.exists(checkpointPath):
            os.remove(checkpointPath)

        console.print(f"  [green]Saved {totalRecords:,} rows to {outputFile}[/green]")
        return outputFile

    def fetchRegion(
        self,
        regionName: str,
        metric: str = "env.temperature",
        start: str = "-7d"
    ) -> List[str]:
        """
        Fetch data for all nodes in a region.

        Args:
            regionName: Region name
            metric: Metric to fetch
            start: Start time

        Returns:
            List of output filenames
        """
        nodes = self.getNodesInRegion(regionName)
        if nodes.empty:
            console.print(f"[red]No nodes found in '{regionName}'.[/red]")
            return []

        console.print(f"[green]Found {len(nodes)} nodes in {regionName}. Starting extraction...[/green]")

        outputs = []
        for vsn in nodes['vsn']:
            result = self.fetch(vsn, metric, start, "now", "7d", None)
            if result:
                outputs.append(result)

        return outputs


def main():
    """Entry point for CLI invocation."""
    pro = BeeHivePro()
    parser = argparse.ArgumentParser(description="BeeHive Pro - Region-based data extraction")
    subparsers = parser.add_subparsers(dest="command")

    # Sync command
    subparsers.add_parser("sync", help="Sync node registry from API")

    # Region command
    regionParser = subparsers.add_parser("region", help="Fetch data for an entire region")
    regionParser.add_argument("name", help="Region name (e.g., 'Chicago', 'Illinois', 'Outside USA')")
    regionParser.add_argument("--metric", default="env.temperature", help="Metric to fetch")
    regionParser.add_argument("--start", default="-7d", help="Start time")

    # List command
    listParser = subparsers.add_parser("list", help="List nodes in a region")
    listParser.add_argument("name", help="Region name")

    args = parser.parse_args()

    if args.command == "sync":
        pro.syncRegistry()
    elif args.command == "region":
        pro.fetchRegion(args.name, args.metric, args.start)
    elif args.command == "list":
        nodes = pro.getNodesInRegion(args.name)
        if nodes.empty:
            console.print(f"[red]No nodes found in '{args.name}'[/red]")
        else:
            table = Table(title=f"Nodes in {args.name}")
            table.add_column("VSN", style="cyan")
            table.add_column("Latitude", style="green")
            table.add_column("Longitude", style="green")
            for _, row in nodes.iterrows():
                table.add_row(
                    row['vsn'],
                    f"{row['lat']:.4f}" if pd.notnull(row['lat']) else "N/A",
                    f"{row['lon']:.4f}" if pd.notnull(row['lon']) else "N/A"
                )
            console.print(table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
