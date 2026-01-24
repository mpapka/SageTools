#!/usr/bin/env python3
"""
Multi-file temperature comparison plotting.

Generates comparison plots overlaying data from multiple CSV files.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
from typing import List


def plotComparison(
    inputFiles: List[str],
    output: str = None,
    title: str = "Temperature Comparison",
    rolling: str = "1h"
) -> bool:
    """
    Compare multiple temperature CSV files on one plot.

    Args:
        inputFiles: List of CSV file paths
        output: Path to save the plot (if None, displays interactively)
        title: Plot title
        rolling: Rolling average window (e.g., "1h", "1d")

    Returns:
        True on success
    """
    plt.figure(figsize=(12, 7))

    # Use a color cycle
    propCycle = plt.rcParams['axes.prop_cycle']
    colors = propCycle.by_key()['color']

    plotted = 0

    for i, filepath in enumerate(inputFiles):
        if not os.path.exists(filepath):
            print(f"Warning: File {filepath} not found. Skipping.")
            continue

        print(f"Processing {filepath}...")
        try:
            # on_bad_lines='skip' ensures we can plot even if some rows are malformed
            df = pd.read_csv(filepath, low_memory=False, on_bad_lines='skip')
            if df.empty:
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

            vsn = df['meta.vsn'].iloc[0] if 'meta.vsn' in df.columns else os.path.basename(filepath)
            color = colors[i % len(colors)]

            # Plot raw data (very transparent dots)
            plt.plot(df['timestamp'], df['value'], ',', color=color, alpha=0.05, linestyle='none')

            # Calculate and plot rolling average
            df = df.set_index('timestamp')
            rollingAvg = df['value'].rolling(window=rolling, min_periods=1).mean()
            plt.plot(rollingAvg.index, rollingAvg.values, label=f"Node {vsn}", color=color, linewidth=1.5)

            plotted += 1

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    if plotted == 0:
        print("No data to plot.")
        return False

    plt.xlabel("Time")
    plt.ylabel("Temperature (C)")
    plt.ylim(-50, 125)
    plt.title(title)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    if output:
        plt.savefig(output)
        print(f"Comparison saved to {output}")
    else:
        plt.show()

    return True


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Compare multiple temperature CSV files on one plot.")
    parser.add_argument("inputFiles", nargs="+", help="Path to one or more CSV files")
    parser.add_argument("--output", help="Path to save the plot (e.g., comparison.pdf)")
    parser.add_argument("--title", default="Temperature Comparison", help="Plot title")
    parser.add_argument("--rolling", default="1h", help="Rolling average window (e.g., 1h, 1d)")

    args = parser.parse_args()

    plotComparison(args.inputFiles, args.output, args.title, args.rolling)


if __name__ == "__main__":
    main()
