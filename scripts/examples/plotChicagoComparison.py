#!/usr/bin/env python3
"""
Enhanced Chicago temperature comparison plot.

Compares multiple Chicago temperature datasets with high-fidelity styling,
QC filtering for impossible temperatures, and Fahrenheit conversion.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse


def plotEnhancedComparison():
    parser = argparse.ArgumentParser(description="Compare multiple Chicago temperature datasets with high-fidelity styling.")
    parser.add_argument("inputFiles", nargs="+", help="Path to one or more CSV files")
    parser.add_argument("--output", help="Path to save the plot (e.g., chicago_comparison.pdf)")
    parser.add_argument("--title", default="Chicago Temperature Comparison (Multi-Node)", help="Plot title")
    parser.add_argument("--rolling", default="1h", help="Rolling average window (e.g., 1h, 6h, 1d)")
    parser.add_argument("--alpha", type=float, default=0.02, help="Alpha transparency for raw data dots")
    parser.add_argument("--sensor", help="Filter by specific sensor name (e.g., bme280, bme680)")

    args = parser.parse_args()

    plt.figure(figsize=(14, 8))

    # Use a high-contrast color cycle for lines
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    for i, file in enumerate(args.inputFiles):
        if not os.path.exists(file):
            print(f"Warning: File {file} not found. Skipping.")
            continue

        print(f"Processing {file}...")
        try:
            # Load data
            df = pd.read_csv(file, low_memory=False, on_bad_lines='skip')
            if df.empty:
                continue

            # Optional sensor filter
            if args.sensor and 'meta.sensor' in df.columns:
                df = df[df['meta.sensor'] == args.sensor]
                if df.empty:
                    print(f"  No data for sensor {args.sensor} in {file}. skipping.")
                    continue

            # Ensure value is numeric and drop invalid rows
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            # Convert Celsius to Fahrenheit
            df['value'] = (df['value'] * 9/5) + 32

            # QC FILTER: Remove impossible ambient temperatures
            df = df[(df['value'] > -40) & (df['value'] < 115)]

            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp', 'value'])
            df = df.sort_values('timestamp')

            vsn = df['meta.vsn'].iloc[0] if 'meta.vsn' in df.columns and pd.notnull(df['meta.vsn'].iloc[0]) else os.path.basename(file)
            color = colors[i % len(colors)]

            # Plot raw data (one pixel dots)
            rawSample = df
            if len(df) > 500000:
                rawSample = df.sample(500000).sort_values('timestamp')

            plt.plot(rawSample['timestamp'], rawSample['value'], ',', color=color,
                     alpha=args.alpha, linestyle='none', rasterized=True)

            # Calculate rolling average
            data = df.set_index('timestamp')
            rollingAvg = data['value'].rolling(window=args.rolling, min_periods=1).mean()
            data = data.reset_index()
            data['rolling'] = rollingAvg.values

            # Identify gaps
            diff = data['timestamp'].diff()
            if len(diff) > 1:
                medianInterval = diff.median()
                gapThreshold = medianInterval * 5
                gapIndices = data.index[diff > gapThreshold].tolist()

                if gapIndices:
                    newRows = []
                    for idx in gapIndices:
                        gapTime = data.loc[idx, 'timestamp'] - (diff[idx] / 2)
                        newRow = data.loc[idx].copy()
                        newRow['timestamp'] = gapTime
                        newRow['rolling'] = float('nan')
                        newRows.append(newRow)
                    data = pd.concat([data, pd.DataFrame(newRows)]).sort_values('timestamp')

            # Plot rolling average line
            plt.plot(data['timestamp'], data['rolling'], color=color, linewidth=2, label=f"Node {vsn}", alpha=0.9)

        except Exception as e:
            print(f"Error processing {file}: {e}")

    plt.xlabel("Time")
    plt.ylabel("Temperature (F)")
    plt.ylim(-60, 140)
    plt.title(args.title)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), markerscale=5)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    if args.output:
        plt.savefig(args.output, dpi=300)
        print(f"Enhanced comparison saved to {args.output}")
    else:
        print("Displaying plot...")
        plt.show()


if __name__ == "__main__":
    plotEnhancedComparison()
