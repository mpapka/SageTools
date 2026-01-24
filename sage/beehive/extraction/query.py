#!/usr/bin/env python3
"""
Simple Sage Beehive data query.

Provides a straightforward interface for querying Beehive data with
optional filtering and CSV export.
"""

import sage_data_client
import argparse
import pandas as pd
from typing import Optional


def runQuery(
    start: str = "-1h",
    end: str = "now",
    name: str = "env.temperature",
    node: str = None,
    vsn: str = None,
    output: str = None,
    url: str = None
) -> Optional[pd.DataFrame]:
    """
    Query Sage Beehive data.

    Args:
        start: Start time (e.g., "-1h", "2023-01-01T00:00:00Z")
        end: End time (e.g., "now", "2023-01-01T01:00:00Z")
        name: Metric name (e.g., "env.temperature", "env.humidity")
        node: Filter by node ID (optional)
        vsn: Filter by VSN (optional)
        output: Save output to CSV file (optional)
        url: Override Sage Data API URL (optional)

    Returns:
        DataFrame with query results, or None on error
    """
    if url:
        sage_data_client.endpoint = url

    queryFilter = {"name": name}
    if node:
        queryFilter["node"] = node
    if vsn:
        queryFilter["vsn"] = vsn

    print(f"Querying Beehive for {name} from {start} to {end}...")

    try:
        df = sage_data_client.query(
            start=start,
            end=end,
            filter=queryFilter
        )

        if df.empty:
            print("No data found for the given parameters. Try a different time range or metric.")
            return None

        print(f"Retrieved {len(df)} records.")
        print("\nFirst few rows:")
        print(df.head())

        if output:
            df.to_csv(output, index=False)
            print(f"\nData saved to {output}")

        return df

    except Exception as e:
        print(f"Error querying Beehive: {e}")
        if "500" in str(e):
            print("Tip: A 500 error often indicates a server-side issue or a query that is too broad. "
                  "Try narrowing your time range or using a different metric (e.g., sys.uptime).")
        return None


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Query Sage Beehive data.")
    parser.add_argument("--start", default="-1h", help="Start time (e.g., -1h, 2023-01-01T00:00:00Z)")
    parser.add_argument("--end", default="now", help="End time (e.g., now, 2023-01-01T01:00:00Z)")
    parser.add_argument("--name", default="env.temperature", help="Metric name (e.g., env.temperature, env.humidity)")
    parser.add_argument("--node", help="Filter by node ID (e.g., W01B)")
    parser.add_argument("--vsn", help="Filter by VSN (e.g., W01B)")
    parser.add_argument("--output", help="Save output to CSV file")
    parser.add_argument("--url", help="Override Sage Data API URL")

    args = parser.parse_args()

    runQuery(
        start=args.start,
        end=args.end,
        name=args.name,
        node=args.node,
        vsn=args.vsn,
        output=args.output,
        url=args.url
    )


if __name__ == "__main__":
    main()
