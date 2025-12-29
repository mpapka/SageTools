#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
import os
import warnings

# Silence warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def plotStrictComparison():
    parser = argparse.ArgumentParser(description="Chicago Climate Comparison with Strict Hardware Validation.")
    parser.add_argument("inputFiles", nargs="+", help="CSV files")
    parser.add_argument("--output", default="chicago_validated.png", help="Output file")
    parser.add_argument("--rolling", default="1h", help="Rolling window")

    args = parser.parse_args()

    plt.figure(figsize=(14, 8))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#bcbd22', '#17becf']

    valid_lines = 0

    for i, file in enumerate(args.inputFiles):
        if not os.path.exists(file): continue
        print(f"Validating hardware for {file}...")
        
        try:
            # Load data
            df = pd.read_csv(file, low_memory=False, on_bad_lines='skip')
            if df.empty: continue
            
            # --- PRE-PROCESSING ---
            # 1. Convert to datetime and REMOVE timezone (makes matplotlib much happier)
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.tz_localize(None)
            # 2. Ensure numeric values
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            # 3. Drop any rows that failed conversion
            df = df.dropna(subset=['timestamp', 'value'])
            if df.empty: continue
            
            # 4. Convert to Fahrenheit
            df['value_f'] = (df['value'] * 9/5) + 32
            
            # --- HARDWARE VALIDATION LOGIC ---
            group_cols = []
            if 'meta.sensor' in df.columns: group_cols.append('meta.sensor')
            if 'meta.host' in df.columns: group_cols.append('meta.host')
            
            if not group_cols:
                group_cols = ['meta.vsn'] 

            groups = df.groupby(group_cols)
            for name, group in groups:
                # Test 1: No extreme failure values
                has_failures = ((group['value_f'] < -45) | (group['value_f'] > 150)).any()
                # Test 2: No evidence of internal CPU heating
                # We use 125F as a safe upper bound for ambient air (Chicago record is 105F)
                is_internal = (group['value_f'] > 125).any()
                
                sensor_id = name if isinstance(name, str) else "-".join([str(x) for x in name])
                
                if has_failures or is_internal:
                    print(f"  ❌ Rejecting sensor {sensor_id}: Hardware failure or internal bias detected.")
                    continue
                
                if group.empty: continue
                
                print(f"  ✅ Accepting sensor {sensor_id}: Valid ambient profile.")
                
                # Plot the validated sensor
                color = colors[valid_lines % len(colors)]
                vsn = group['meta.vsn'].iloc[0] if 'meta.vsn' in group.columns else "Node"
                
                # Plot density dots
                plt.plot(group['timestamp'], group['value_f'], ',', color=color, alpha=0.02, linestyle='none', rasterized=True)
                
                # Plot rolling average
                group = group.sort_values('timestamp').set_index('timestamp')
                rolling = group['value_f'].rolling(window=args.rolling, min_periods=1).mean()
                
                plt.plot(rolling.index, rolling.values, color=color, linewidth=2, label=f"{vsn} ({sensor_id})")
                valid_lines += 1

        except Exception as e:
            print(f"Error: {e}")

    plt.xlabel("Time")
    plt.ylabel("Temperature (°F)")
    plt.ylim(-40, 110) # Focused ambient range
    plt.title("Chicago Validated Ambient Temperature (Faulty Hardware Excluded)")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    plt.savefig(args.output, dpi=300)
    print(f"\nSaved validated plot to {args.output}")

if __name__ == "__main__":
    plotStrictComparison()
