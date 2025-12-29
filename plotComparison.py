#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os

def plotComparison():
    parser = argparse.ArgumentParser(description="Compare multiple temperature CSV files on one plot.")
    parser.add_argument("inputFiles", nargs="+", help="Path to one or more CSV files")
    parser.add_argument("--output", help="Path to save the plot (e.g. comparison.pdf)")
    parser.add_argument("--title", default="Temperature Comparison", help="Plot title")
    parser.add_argument("--rolling", default="1h", help="Rolling average window (e.g. 1h, 1d)")

    args = parser.parse_args()

    plt.figure(figsize=(12, 7))
    
    # Use a color cycle
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']

    for i, file in enumerate(args.inputFiles):
        if not os.path.exists(file):
            print(f"Warning: File {file} not found. Skipping.")
            continue
            
        print(f"Processing {file}...")
        try:
            # on_bad_lines='skip' ensures we can plot even if some rows are malformed
            df = pd.read_csv(file, low_memory=False, on_bad_lines='skip')
            if df.empty: continue
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            vsn = df['meta.vsn'].iloc[0] if 'meta.vsn' in df.columns else os.path.basename(file)
            color = colors[i % len(colors)]

            # Plot raw data (very transparent dots)
            plt.plot(df['timestamp'], df['value'], ',', color=color, alpha=0.05, linestyle='none')
            
            # Calculate and plot rolling average
            df = df.set_index('timestamp')
            rolling = df['value'].rolling(window=args.rolling, min_periods=1).mean()
            plt.plot(rolling.index, rolling.values, label=f"Node {vsn}", color=color, linewidth=1.5)

        except Exception as e:
            print(f"Error processing {file}: {e}")

    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.ylim(-50, 125)
    plt.title(args.title)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    if args.output:
        plt.savefig(args.output)
        print(f"Comparison saved to {args.output}")
    else:
        plt.show()

if __name__ == "__main__":
    plotComparison()
