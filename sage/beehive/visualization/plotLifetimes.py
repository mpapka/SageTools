#!/usr/bin/env python3
"""
Node lifetime timeline visualization.

Generates a "tapestry" visualization showing when nodes were active
over time, with color-coding by node type.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import argparse
import os
import json
from typing import Optional


# Color map for node types (VSN prefix)
TYPE_COLORS = {
    'W': '#1f77b4',  # Blue (Waggle)
    'H': '#ff7f0e',  # Orange
    'D': '#2ca02c',  # Green
    'V': '#d62728',  # Red (Virtual)
    'X': '#9467bd',  # Purple
}
DEFAULT_COLOR = '#7f7f7f'  # Gray for unknown


def plotLifetimes(
    inputFile: str = "nodeRegistry.csv",
    output: str = None,
    limit: int = None,
    prefix: str = None,
    minDays: int = None,
    onlyWithLocation: bool = False
) -> bool:
    """
    Visualize the lifetimes of nodes from Beehive registry.

    Args:
        inputFile: Path to nodeRegistry.csv
        output: Path to save the plot (if None, displays interactively)
        limit: Limit number of nodes to display
        prefix: Filter nodes by VSN prefix (e.g., "W08")
        minDays: Filter nodes by minimum lifespan in days
        onlyWithLocation: Only show nodes with valid GPS coordinates

    Returns:
        True on success
    """
    if not os.path.exists(inputFile):
        print(f"Error: File {inputFile} not found. Run listNodes.py first.")
        return False

    print(f"Reading {inputFile}...")
    df = pd.read_csv(inputFile)

    # Filter out any rows with missing dates
    df = df[df['firstSeen'].notnull() & df['lastSeen'].notnull()]

    # Convert to datetime
    df['firstSeen'] = pd.to_datetime(df['firstSeen'])
    df['lastSeen'] = pd.to_datetime(df['lastSeen'])

    # Skip nodes with no life (lastSeen must be strictly after firstSeen)
    initialCount = len(df)
    df = df[df['lastSeen'] > df['firstSeen']]
    if len(df) < initialCount:
        print(f"Skipped {initialCount - len(df)} nodes with zero or negative lifespan.")

    # Apply Filters
    if prefix:
        print(f"Filtering by prefix: {prefix}")
        df = df[df['vsn'].astype(str).str.startswith(prefix)]

    if minDays:
        print(f"Filtering by min lifespan: {minDays} days")
        df['days'] = (df['lastSeen'] - df['firstSeen']).dt.total_seconds() / 86400
        df = df[df['days'] >= minDays]

    if onlyWithLocation:
        print("Filtering for nodes with location data...")
        df = df[df['lat'].notnull() & df['lon'].notnull()]

    # Sort by firstSeen to make the plot look organized
    df = df.sort_values('firstSeen', ascending=False)

    numNodes = len(df) if limit is None else min(len(df), limit)
    if limit and len(df) > limit:
        print(f"Note: Displaying the {limit} most recently deployed nodes out of {len(df)}.")
        df = df.head(limit)

    if numNodes == 0:
        print("No nodes match the specified filters.")
        return False

    # For a "solid" look, we want a taller figure if there are many nodes
    plt.figure(figsize=(14, 8))

    print(f"Plotting {numNodes} nodes as a solid timeline...")

    # Plot each node as horizontal segments based on active periods
    for i, (idx, row) in enumerate(df.iterrows()):
        prefixChar = str(row['vsn'])[0].upper()
        color = TYPE_COLORS.get(prefixChar, DEFAULT_COLOR)

        # Determine linewidth
        width = (72 * 8) / numNodes if numNodes > 0 else 5

        # Check if we have activePeriods (tuples)
        hasPeriods = False
        if 'activePeriods' in row and pd.notnull(row['activePeriods']):
            try:
                periods = json.loads(row['activePeriods'])
                if periods:
                    hasPeriods = True
                    for start, end in periods:
                        plt.hlines(y=i, xmin=pd.to_datetime(start), xmax=pd.to_datetime(end),
                                   color=color, linewidth=width, alpha=1.0)
            except Exception:
                pass

        # Fallback to simple firstSeen/lastSeen if no periods found
        if not hasPeriods:
            plt.hlines(y=i, xmin=row['firstSeen'], xmax=row['lastSeen'],
                       color=color, linewidth=width, alpha=1.0)

    # Remove Y-axis labels and ticks to pack them close
    plt.yticks([])
    plt.gca().yaxis.set_visible(False)

    # Format X-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    plt.title("Sage Beehive Node Timeline Tapestry (Colored by Type)")
    plt.xlabel("Timeline")

    # Add a legend for the colors
    legendElements = [Line2D([0], [0], color=c, lw=4, label=f"Type {t}")
                      for t, c in TYPE_COLORS.items() if any(df['vsn'].astype(str).str.startswith(t))]
    if legendElements:
        plt.legend(handles=legendElements, loc='upper left', bbox_to_anchor=(1, 1))

    plt.grid(axis='x', linestyle='--', alpha=0.3)
    plt.tight_layout()

    if output:
        plt.savefig(output)
        print(f"Plot saved to {output}")
    else:
        print("Displaying plot...")
        plt.show()

    return True


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Visualize the lifetimes of nodes from Beehive registry.")
    parser.add_argument("inputFile", default="nodeRegistry.csv", nargs="?", help="Path to nodeRegistry.csv")
    parser.add_argument("--output", help="Path to save the plot (e.g., lifetimes.png)")
    parser.add_argument("--limit", type=int, help="Limit number of nodes to display (default: all)")
    parser.add_argument("--prefix", help="Filter nodes by VSN prefix (e.g., W08)")
    parser.add_argument("--minDays", type=int, help="Filter nodes by minimum lifespan in days")
    parser.add_argument("--onlyWithLocation", action="store_true", help="Only show nodes with valid GPS coordinates")

    args = parser.parse_args()

    plotLifetimes(args.inputFile, args.output, args.limit, args.prefix, args.minDays, args.onlyWithLocation)


if __name__ == "__main__":
    main()
