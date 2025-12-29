#!/usr/bin/env python3
import sage_data_client
import argparse
import pandas as pd
from datetime import datetime

def runQuery():
    parser = argparse.ArgumentParser(description="Query Sage Beehive data.")
    parser.add_argument("--start", default="-1h", help="Start time (e.g. -1h, 2023-01-01T00:00:00Z)")
    parser.add_argument("--end", default="now", help="End time (e.g. now, 2023-01-01T01:00:00Z)")
    parser.add_argument("--name", default="env.temperature", help="Metric name (e.g. env.temperature, env.humidity)")
    parser.add_argument("--node", help="Filter by node ID (e.g. W01B)")
    parser.add_argument("--vsn", help="Filter by VSN (e.g. W01B)")
    parser.add_argument("--output", help="Save output to CSV file")
    parser.add_argument("--url", help="Override Sage Data API URL")

    args = parser.parse_args()

    if args.url:
        sage_data_client.endpoint = args.url

    queryFilter = {"name": args.name}
    if args.node:
        queryFilter["node"] = args.node
    if args.vsn:
        queryFilter["vsn"] = args.vsn

    print(f"Querying Beehive for {args.name} from {args.start} to {args.end}...")
    
    try:
        df = sage_data_client.query(
            start=args.start,
            end=args.end,
            filter=queryFilter
        )

        if df.empty:
            print("No data found for the given parameters. Try a different time range or metric.")
            return

        print(f"Retrieved {len(df)} records.")
        print("\nFirst few rows:")
        print(df.head())

        if args.output:
            df.to_csv(args.output, index=False)
            print(f"\nData saved to {args.output}")

    except Exception as e:
        print(f"Error querying Beehive: {e}")
        if "500" in str(e):
            print("Tip: A 500 error often indicates a server-side issue or a query that is too broad. Try narrowing your time range or using a different metric (e.g., sys.uptime).")


if __name__ == "__main__":
    runQuery()
