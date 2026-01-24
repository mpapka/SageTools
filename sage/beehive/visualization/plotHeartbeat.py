#!/usr/bin/env python3
"""
Node activity heartbeat tapestry visualization.

Generates a visualization showing when nodes were active vs inactive
over time by querying the Beehive API for each time bin.
"""

import sage_data_client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import argparse
import os
from datetime import datetime, timedelta
from typing import Optional


# Color map for node types (VSN prefix)
TYPE_COLORS = {
    'W': '#1f77b4',  # Blue (Waggle)
    'H': '#ff7f0e',  # Orange
    'D': '#2ca02c',  # Green
    'V': '#d62728',  # Red (Virtual)
    'X': '#9467bd',  # Purple
}
DEFAULT_COLOR = '#7f7f7f'


def plotHeartbeat(
    inputFile: str = "nodeRegistry.csv",
    output: str = None,
    binSize: str = "1w",
    prefix: str = None
) -> bool:
    """
    Create a Heartbeat Tapestry showing when nodes were active.

    Args:
        inputFile: Path to nodeRegistry.csv
        output: Path to save the plot (if None, displays interactively)
        binSize: Time slice for activity check (e.g., "1d", "1w", "1m")
        prefix: Filter by VSN prefix (e.g., "W08")

    Returns:
        True on success
    """
    if not os.path.exists(inputFile):
        print("Error: nodeRegistry.csv not found.")
        return False

    registry = pd.read_csv(inputFile)
    registry['firstSeen'] = pd.to_datetime(registry['firstSeen'])
    registry['lastSeen'] = pd.to_datetime(registry['lastSeen'])

    if prefix:
        registry = registry[registry['vsn'].astype(str).str.startswith(prefix)]

    vsnList = sorted(registry['vsn'].unique().tolist())
    numNodes = len(vsnList)

    if numNodes == 0:
        print("No nodes found matching filters.")
        return False

    globalStart = registry['firstSeen'].min()
    globalEnd = registry['lastSeen'].max()

    # Determine bin delta
    unit = binSize[-1]
    val = int(binSize[:-1])
    if unit == 'd':
        delta = timedelta(days=val)
    elif unit == 'w':
        delta = timedelta(weeks=val)
    elif unit == 'm':
        delta = timedelta(days=30*val)
    else:
        delta = timedelta(weeks=1)

    print(f"Building heartbeat map for {numNodes} nodes...")
    print(f"Granularity: {binSize} | Range: {globalStart.date()} to {globalEnd.date()}")

    # Matrix: Row = Node, Col = Bin (Boolean: Active/Inactive)
    activityMap = []

    currentStart = globalStart
    bins = []

    while currentStart < globalEnd:
        currentEnd = currentStart + delta
        bins.append(currentStart)

        print(f"  Probing {currentStart.date()}...", end="\r")
        try:
            # Efficiently query which nodes were alive in this window
            activeInWindow = sage_data_client.query(
                start=currentStart.strftime('%Y-%m-%dT%H:%M:%SZ'),
                end=currentEnd.strftime('%Y-%m-%dT%H:%M:%SZ'),
                filter={"name": "sys.uptime"},
                tail=1
            )

            seenVsns = set()
            if not activeInWindow.empty:
                seenVsns = set(activeInWindow['meta.vsn'].unique())

            activityMap.append([vsn in seenVsns for vsn in vsnList])
        except Exception:
            activityMap.append([False] * numNodes)

        currentStart = currentEnd

    print("\nPlotting Tapestry...")
    plt.figure(figsize=(14, 8))

    # We use broken_barh to plot the segments where the node was active
    for i, vsn in enumerate(vsnList):
        prefixChar = vsn[0].upper()
        color = TYPE_COLORS.get(prefixChar, DEFAULT_COLOR)

        # Calculate segments of "True" in activityMap for this node
        activeSegments = []
        startIdx = None

        for bIdx, activeInBin in enumerate(activityMap):
            isActive = activeInBin[i]
            if isActive and startIdx is None:
                startIdx = bIdx
            elif not isActive and startIdx is not None:
                # End of a segment
                activeSegments.append((
                    mdates.date2num(bins[startIdx]),
                    mdates.date2num(bins[bIdx]) - mdates.date2num(bins[startIdx])
                ))
                startIdx = None

        if startIdx is not None:
            activeSegments.append((
                mdates.date2num(bins[startIdx]),
                mdates.date2num(globalEnd) - mdates.date2num(bins[startIdx])
            ))

        if activeSegments:
            # Height of bars is 1.0 to make them touch
            plt.broken_barh(activeSegments, (i, 1.0), color=color, linewidth=0)

    plt.yticks([])
    plt.gca().yaxis.set_visible(False)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.title(f"Sage Beehive Heartbeat Tapestry ({binSize} resolution)")

    # Legend
    legendElements = [Line2D([0], [0], color=c, lw=4, label=f"Type {t}")
                      for t, c in TYPE_COLORS.items() if any(registry['vsn'].astype(str).str.startswith(t))]
    if legendElements:
        plt.legend(handles=legendElements, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()

    if output:
        plt.savefig(output)
        print(f"Heartbeat saved to {output}")
    else:
        plt.show()

    return True


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Create a Heartbeat Tapestry showing when nodes were active.")
    parser.add_argument("inputFile", default="nodeRegistry.csv", nargs="?", help="Path to nodeRegistry.csv")
    parser.add_argument("--output", help="Path to save the plot (e.g., heartbeat.pdf)")
    parser.add_argument("--binSize", default="1w", help="Time slice for activity check (e.g., 1d, 1w, 1m)")
    parser.add_argument("--prefix", help="Filter by VSN prefix (e.g., W08)")

    args = parser.parse_args()

    plotHeartbeat(args.inputFile, args.output, args.binSize, args.prefix)


if __name__ == "__main__":
    main()
