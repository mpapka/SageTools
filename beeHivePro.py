#!/usr/bin/env python3
import sage_data_client
import pandas as pd
import argparse
import os
import json
import sys
import time
import warnings
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parseDate
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel

# --- CONFIGURATION ---
console = Console()
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

class RegionManager:
    def __init__(self, configFile="regions.json"):
        self.configFile = configFile
        self.regions = self.load()

    def load(self):
        if os.path.exists(self.configFile):
            with open(self.configFile, 'r') as f:
                return json.load(f)
        # Default starter regions
        defaults = {
            "usa": {"lat": [24.0, 49.0], "lon": [-125.0, -66.0]}
        }
        self.save(defaults)
        return defaults

    def save(self, data):
        with open(self.configFile, 'w') as f:
            json.dump(data, f, indent=4)

    def get_bbox(self, query):
        query_key = query.lower().replace(" ", "_")
        if query_key in self.regions:
            return self.regions[query_key]

        # Dynamic Lookup via OpenStreetMap (Nominatim)
        console.print(f"[yellow]Searching for boundaries of '{query}' online...[/yellow]")
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
            headers = {'User-Agent': 'BeeHivePro/1.0 (Educational Tool)'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if data:
                    bbox = [float(x) for x in data[0]['boundingbox']]
                    # OSM order: [minLat, maxLat, minLon, maxLon]
                    res = {"lat": [bbox[0], bbox[1]], "lon": [bbox[2], bbox[3]]}
                    self.regions[query_key] = res
                    self.save(self.regions)
                    return res
        except Exception as e:
            console.print(f"[red]Could not find region '{query}': {e}[/red]")
        return None

class BeeHivePro:
    def __init__(self):
        self.registryFile = "nodeRegistry.csv"
        self.registry = None
        self.regions = RegionManager()

    def loadRegistry(self, forceUpdate=False):
        if not os.path.exists(self.registryFile) or forceUpdate:
            self.syncRegistry()
        self.registry = pd.read_csv(self.registryFile)
        self.registry['vsn'] = self.registry['vsn'].astype(str)

    def syncRegistry(self):
        try:
            with console.status("[bold green]Syncing Global Node Registry (including GPS)...") as status:
                birthDf = sage_data_client.query(start="2018-01-01T00:00:00Z", head=1, filter={"name": "sys.uptime"})
                deathDf = sage_data_client.query(start="2018-01-01T00:00:00Z", tail=1, filter={"name": "sys.uptime"})
                gpsLat = sage_data_client.query(start="2018-01-01T00:00:00Z", filter={"name": "sys.gps.lat"}, tail=1)
                gpsLon = sage_data_client.query(start="2018-01-01T00:00:00Z", filter={"name": "sys.gps.lon"}, tail=1)
                
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
        except Exception as e:
            console.print(f"[red]Sync failed: {e}[/red]")

    def getNodesInRegion(self, regionQuery):
        self.loadRegistry()
        
        is_outside = False
        if regionQuery.lower().startswith("outside "):
            is_outside = True
            regionQuery = regionQuery[8:]

        bbox = self.regions.get_bbox(regionQuery)
        if not bbox: return pd.DataFrame()
            
        mask = (self.registry['lat'] >= bbox['lat'][0]) & (self.registry['lat'] <= bbox['lat'][1]) & \
               (self.registry['lon'] >= bbox['lon'][0]) & (self.registry['lon'] <= bbox['lon'][1])
        
        if is_outside:
            return self.registry[~mask & self.registry['lat'].notnull()]
        return self.registry[mask]

    def fetch(self, vsn, metric, startStr, endStr, targetChunkStr, output):
        self.loadRegistry()
        endTime = datetime.now(timezone.utc) if endStr == "now" else parseDate(endStr).replace(tzinfo=timezone.utc)
        
        if startStr == "all":
            nodeInfo = self.registry[self.registry['vsn'] == vsn]
            if nodeInfo.empty: return
            startTime = pd.to_datetime(nodeInfo['firstSeen'].iloc[0]).to_pydatetime()
            if startTime.tzinfo is None: startTime = startTime.replace(tzinfo=timezone.utc)
        else:
            startTime = (endTime - timedelta(days=int(startStr[1:-1]))) if startStr.startswith("-") else parseDate(startStr).replace(tzinfo=timezone.utc)

        metricSafe = metric.replace('.','').title().replace(' ','')
        metricSafe = metricSafe[0].lower() + metricSafe[1:]
        outputFile = output if output else f"{metricSafe}{vsn}Pro.csv"
        checkpointPath = f".{outputFile}.checkpoint"
        
        if os.path.exists(checkpointPath):
            with open(checkpointPath, 'r') as f:
                startTime = parseDate(json.load(f)['lastProcessedTimestamp']).replace(tzinfo=timezone.utc)

        unit = targetChunkStr[-1]
        targetDuration = timedelta(days=int(targetChunkStr[:-1])) if unit == 'd' else timedelta(hours=int(targetChunkStr[:-1]))
        currentDuration, currentStart, totalRecords, writeHeader = targetDuration, startTime, 0, not os.path.exists(outputFile)

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), 
                      TaskProgressColumn(), TimeElapsedColumn(), TimeRemainingColumn(), console=console) as progress:
            mainTask = progress.add_task(f"Fetching {vsn}", total=(endTime - startTime).total_seconds())
            while currentStart < endTime:
                currentEnd = min(currentStart + currentDuration, endTime)
                startIso, endIso = currentStart.strftime('%Y-%m-%dT%H:%M:%SZ'), currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ')
                try:
                    durDays = currentDuration.total_seconds() / 86400
                    progress.update(mainTask, description=f"Node {vsn} ({durDays:.1f}d chunk)")
                    df = sage_data_client.query(start=startIso, end=endIso, filter={"name": metric, "vsn": vsn})
                    if not df.empty:
                        if os.path.exists(outputFile) and not writeHeader:
                            df = df.reindex(columns=pd.read_csv(outputFile, nrows=0).columns.tolist())
                        df.to_csv(outputFile, mode='a', index=False, header=writeHeader)
                        writeHeader, totalRecords = False, totalRecords + len(df)
                    with open(checkpointPath, 'w') as f: json.dump({"lastProcessedTimestamp": endIso}, f)
                    progress.advance(mainTask, (currentEnd - currentStart).total_seconds())
                    currentStart, currentDuration = currentEnd, min(currentDuration * 2, targetDuration)
                except Exception as e:
                    if "500" in str(e):
                        currentDuration = max(currentDuration / 2, timedelta(hours=1))
                        time.sleep(1)
                    else: sys.exit(1)
        if os.path.exists(checkpointPath): os.remove(checkpointPath)
        console.print(f"  [green]Saved {totalRecords:,} rows to {outputFile}[/green]")

def main():
    pro = BeeHivePro()
    parser = argparse.ArgumentParser(description="BeeHive Pro")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("sync")
    
    r_parser = subparsers.add_parser("region", help="Fetch data for an entire region")
    r_parser.add_argument("name", help="Region name (e.g. 'Chicago', 'Illinois', 'Outside USA')")
    r_parser.add_argument("--metric", default="env.temperature")
    r_parser.add_argument("--start", default="-7d")
    
    args = parser.parse_args()
    if args.command == "sync": pro.syncRegistry()
    elif args.command == "region":
        nodes = pro.getNodesInRegion(args.name)
        if nodes.empty:
            console.print(f"[red]No nodes found in '{args.name}'.[/red]")
            return
        console.print(f"[green]Found {len(nodes)} nodes in {args.name}. Starting extraction...[/green]")
        for vsn in nodes['vsn']: pro.fetch(vsn, args.metric, args.start, "now", "7d", None)
    else: parser.print_help()

if __name__ == "__main__": main()