#!/usr/bin/env python3
import sage_data_client
import pandas as pd
import argparse
import json
import warnings
from datetime import datetime, timedelta

# Silence persistent pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

def listAllNodes():
    print("Fetching node registry from Beehive (this may take a minute)...")
    
    try:
        # 1. Get the first ever record for each node to determine "Birth"
        print("Searching for first contact (Birth) for all nodes...")
        birthDf = sage_data_client.query(
            start="2018-01-01T00:00:00Z",
            head=1,
            filter={"name": "sys.uptime"}
        )
        
        # 2. Get the last ever record for each node to determine "Last Seen"
        print("Searching for last contact (End of Life) for all nodes...")
        deathDf = sage_data_client.query(
            start="2018-01-01T00:00:00Z",
            tail=1,
            filter={"name": "sys.uptime"}
        )
        
        if birthDf.empty or deathDf.empty:
            print("No node data found.")
            return

        # Prepare base info
        availableCols = birthDf.columns.tolist()
        neededCols = ['meta.vsn', 'timestamp']
        if 'meta.lat' in availableCols: neededCols.append('meta.lat')
        if 'meta.lon' in availableCols: neededCols.append('meta.lon')
            
        birthInfo = birthDf[neededCols].copy()
        renameMap = {'meta.vsn': 'vsn', 'timestamp': 'firstSeen'}
        if 'meta.lat' in availableCols: renameMap['meta.lat'] = 'lat'
        if 'meta.lon' in availableCols: renameMap['meta.lon'] = 'lon'
        birthInfo.columns = [renameMap.get(c, c) for c in birthInfo.columns]
        birthInfo = birthInfo.sort_values('firstSeen').drop_duplicates('vsn')
        
        # Ensure lat/lon columns exist
        if 'lat' not in birthInfo.columns: birthInfo['lat'] = None
        if 'lon' not in birthInfo.columns: birthInfo['lon'] = None
        
        deathInfo = deathDf[['meta.vsn', 'timestamp']].copy()
        deathInfo.columns = ['vsn', 'lastSeen']
        deathInfo = deathInfo.sort_values('lastSeen', ascending=False).drop_duplicates('vsn')
        
        birthInfo['vsn'] = birthInfo['vsn'].astype(str)
        deathInfo['vsn'] = deathInfo['vsn'].astype(str)
        
        # Merge and clean
        nodes = pd.merge(birthInfo, deathInfo, on='vsn')
        nodes = nodes[nodes['vsn'].astype(str).str.lower() != 'nan']
        nodes['firstSeen'] = pd.to_datetime(nodes['firstSeen'])
        nodes['lastSeen'] = pd.to_datetime(nodes['lastSeen'])
        nodes = nodes[nodes['lastSeen'] >= nodes['firstSeen']]
        
        # --- Recover ALL historical locations ---
        print("Recovering historical locations from sys.gps metrics...")
        try:
            # We query the entire history but only take the latest 1 record per node
            allGpsLat = sage_data_client.query(start="2018-01-01T00:00:00Z", filter={"name": "sys.gps.lat"}, tail=1)
            allGpsLon = sage_data_client.query(start="2018-01-01T00:00:00Z", filter={"name": "sys.gps.lon"}, tail=1)
            
            if not allGpsLat.empty:
                latMap = dict(zip(allGpsLat['meta.vsn'].astype(str), allGpsLat['value']))
                nodes['lat'] = nodes['lat'].fillna(nodes['vsn'].map(latMap))
            if not allGpsLon.empty:
                lonMap = dict(zip(allGpsLon['meta.vsn'].astype(str), allGpsLon['value']))
                nodes['lon'] = nodes['lon'].fillna(nodes['vsn'].map(lonMap))
        except Exception as gpsErr:
            print(f"  Warning: GPS recovery failed: {gpsErr}")

        # --- Capture Active Periods (Tuples) ---
        print("Mapping active periods (weekly granularity)...")
        binDelta = timedelta(weeks=1)
        globalStart = nodes['firstSeen'].min()
        globalEnd = nodes['lastSeen'].max()
        
        activityData = {vsn: [] for vsn in nodes['vsn']}
        currentStart = globalStart
        
        while currentStart < globalEnd:
            currentEnd = currentStart + binDelta
            print(f"  Probing: {currentStart.date()} to {currentEnd.date()}...", end="\r")
            try:
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
                            if activityData[vsn] and activityData[vsn][-1][1] == currentStart.isoformat():
                                activityData[vsn][-1] = (activityData[vsn][-1][0], currentEnd.isoformat())
                            else:
                                activityData[vsn].append((currentStart.isoformat(), currentEnd.isoformat()))
            except Exception:
                pass
            currentStart = currentEnd
        
        nodes['activePeriods'] = nodes['vsn'].map(lambda x: json.dumps(activityData.get(x, [])))

        # Final Formatting
        nodes = nodes.sort_values('vsn')
        print("\n" + "-" * 100)
        print(f"{ 'VSN':<8} | { 'Lat':<10} | { 'Lon':<10} | { 'First Seen':<20} | { 'Activity'}")
        print("-" * 100)
        
        for _, row in nodes.iterrows():
            lat = f"{row['lat']:.4f}" if pd.notnull(row['lat']) else "N/A"
            lon = f"{row['lon']:.4f}" if pd.notnull(row['lon']) else "N/A"
            periods = json.loads(row['activePeriods'])
            print(f"{row['vsn']:<8} | {lat:<10} | {lon:<10} | {str(row['firstSeen'])[:19]:<20} | {len(periods)} active blocks")

        filename = "nodeRegistry.csv"
        nodes.to_csv(filename, index=False)
        print("-" * 100)
        print(f"Total valid nodes found: {len(nodes)}")
        print(f"Registry saved to {filename}")

    except Exception as e:
        print(f"Error retrieving node registry: {e}")

if __name__ == "__main__":
    listAllNodes()