#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os

def plotLifetimes():
    parser = argparse.ArgumentParser(description="Visualize the lifetimes of nodes from Beehive registry.")
    parser.add_argument("inputFile", default="nodeRegistry.csv", nargs="?", help="Path to nodeRegistry.csv")
    parser.add_argument("--output", help="Path to save the plot (e.g. lifetimes.png)")
    parser.add_argument("--limit", type=int, help="Limit number of nodes to display (default: all)")
    parser.add_argument("--prefix", help="Filter nodes by VSN prefix (e.g. W08)")
    parser.add_argument("--minDays", type=int, help="Filter nodes by minimum lifespan in days")
    parser.add_argument("--onlyWithLocation", action="store_true", help="Only show nodes with valid GPS coordinates")

    args = parser.parse_args()

    if not os.path.exists(args.inputFile):
        print(f"Error: File {args.inputFile} not found. Run listNodes.py first.")
        return

    print(f"Reading {args.inputFile}...")
    df = pd.read_csv(args.inputFile)
    
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
    if args.prefix:
        print(f"Filtering by prefix: {args.prefix}")
        df = df[df['vsn'].astype(str).str.startswith(args.prefix)]
    
    if args.minDays:
        print(f"Filtering by min lifespan: {args.minDays} days")
        df['days'] = (df['lastSeen'] - df['firstSeen']).dt.total_seconds() / 86400
        df = df[df['days'] >= args.minDays]

    if args.onlyWithLocation:
        print("Filtering for nodes with location data...")
        df = df[df['lat'].notnull() & df['lon'].notnull()]

    # Sort by firstSeen to make the plot look organized
    df = df.sort_values('firstSeen', ascending=False)
    
    numNodes = len(df) if args.limit is None else min(len(df), args.limit)
    if args.limit and len(df) > args.limit:
        print(f"Note: Displaying the {args.limit} most recently deployed nodes out of {len(df)}.")
        df = df.head(args.limit)

    # For a "solid" look, we want a taller figure if there are many nodes
    # but we will also use linewidth to make them touch.
    plt.figure(figsize=(14, 8))
    
    print(f"Plotting {numNodes} nodes as a solid timeline...")
    
    # Define a color map for node types (VSN prefix)
    typeColors = {
        'W': '#1f77b4',  # Blue (Waggle)
        'H': '#ff7f0e',  # Orange
        'D': '#2ca02c',  # Green
        'V': '#d62728',  # Red (Virtual)
        'X': '#9467bd',  # Purple
    }
    defaultColor = '#7f7f7f' # Gray for unknown

    # Plot each node as horizontal segments based on active periods
    for i, (idx, row) in enumerate(df.iterrows()):
        prefix = str(row['vsn'])[0].upper()
        color = typeColors.get(prefix, defaultColor)
        
        # Determine linewidth
        width = (72 * 8) / numNodes if numNodes > 0 else 5
        
        # Check if we have activePeriods (tuples)
        import json
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
    from matplotlib.lines import Line2D
    legendElements = [Line2D([0], [0], color=c, lw=4, label=f"Type {t}") 
                      for t, c in typeColors.items() if any(df['vsn'].astype(str).str.startswith(t))]
    if legendElements:
        plt.legend(handles=legendElements, loc='upper left', bbox_to_anchor=(1, 1))

    plt.grid(axis='x', linestyle='--', alpha=0.3)
    plt.tight_layout()

    if args.output:
        plt.savefig(args.output)
        print(f"Plot saved to {args.output}")
    else:
        print("Displaying plot...")
        plt.show()

if __name__ == "__main__":
    plotLifetimes()
