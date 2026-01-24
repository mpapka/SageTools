#!/usr/bin/env python3
"""
List available metrics for a Sage Beehive node.

Queries recent data for a specific node to discover all available metric names.
"""

import sage_data_client
import pandas as pd
import argparse
from typing import List, Optional


def listMetrics(vsn: str, timeRange: str = "-5m") -> Optional[List[str]]:
    """
    Find all available metrics for a node.

    Args:
        vsn: Node VSN (e.g., "W077")
        timeRange: Time range to search (default: last 5 minutes)

    Returns:
        Sorted list of metric names, or None on error
    """
    print(f"Finding all available metrics for node {vsn} in the last 5 minutes...")
    try:
        # Querying without a 'name' filter to see all metrics for this node
        df = sage_data_client.query(
            start=timeRange,
            filter={"vsn": vsn}
        )
        if df.empty:
            print(f"No data found for node {vsn} recently.")
            return None
        else:
            metrics = sorted(df['name'].unique().tolist())
            print(f"Available metrics for {vsn}:")
            for m in metrics:
                print(f"  - {m}")
            return metrics
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="List available metrics for a Sage node")
    parser.add_argument("vsn", nargs="?", default="W077", help="VSN of the node (e.g., W077)")
    parser.add_argument("--range", "-r", default="-5m", help="Time range to search (default: -5m)")
    args = parser.parse_args()

    listMetrics(args.vsn, args.range)


if __name__ == "__main__":
    main()
