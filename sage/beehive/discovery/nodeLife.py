#!/usr/bin/env python3
"""
Find the first and last data points for a Sage Beehive node.

Investigates the lifetime of a node using sys.uptime as a reliable heartbeat probe.
"""

import sage_data_client
import argparse
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple


def findNodeLife(vsn: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Investigate the lifetime of a node using sys.uptime as a probe.

    Args:
        vsn: Node VSN (e.g., "W077")

    Returns:
        Tuple of (firstSeen, lastSeen) datetimes, or None if not found
    """
    print(f"Investigating lifetime of node {vsn} using 'sys.uptime' as a probe...")

    try:
        # We search for sys.uptime as it is the most reliable "heartbeat" metric
        # and much faster to query than searching all metrics.

        # Find the very last record first (usually fast)
        lastDf = sage_data_client.query(
            start="-7d",  # Start by looking in the last week
            tail=1,
            filter={"vsn": vsn, "name": "sys.uptime"}
        )

        if lastDf.empty:
            # If not in the last week, try a broader search for the end
            lastDf = sage_data_client.query(
                start="2018-01-01T00:00:00Z",
                tail=1,
                filter={"vsn": vsn, "name": "sys.uptime"}
            )

        if lastDf.empty:
            print(f"No 'sys.uptime' records found for node {vsn}. The node might be offline or the VSN is incorrect.")
            return None

        endTime = lastDf['timestamp'].iloc[0]

        # Find the very first record
        # We use a stepwise approach to avoid 504 timeouts on massive scans
        print("Searching for birth date...")

        # Start searching year by year backwards from current year
        currentYear = datetime.now().year
        startTime = None

        for year in range(2020, currentYear + 1):
            print(f"  Checking year {year}...", end="\r")
            probeDf = sage_data_client.query(
                start=f"{year}-01-01T00:00:00Z",
                end=f"{year+1}-01-01T00:00:00Z",
                head=1,
                filter={"vsn": vsn, "name": "sys.uptime"}
            )
            if not probeDf.empty:
                startTime = probeDf['timestamp'].iloc[0]
                break

        if not startTime:
            print(f"\nCould not pinpoint a start date for {vsn}.")
            return None

        duration = endTime - startTime

        print("\n" + "-" * 30)
        print(f"Node VSN:    {vsn}")
        print(f"First Seen:  {startTime}")
        print(f"Last Seen:   {endTime}")
        print(f"Lifetime:    {duration}")
        print("-" * 30)

        # Suggest a command for full life extraction
        print("\nTo extract the full life of this node, you can run:")
        print(f"python -m sage.beehive.extraction.batchQuery --vsn={vsn} --start='{startTime.strftime('%Y-%m-%dT%H:%M:%SZ')}' --end='{endTime.strftime('%Y-%m-%dT%H:%M:%SZ')}' --chunkSize=1d")

        return (startTime, endTime)

    except Exception as e:
        print(f"Error investigating node life: {e}")
        return None


def main():
    """Entry point for CLI invocation."""
    parser = argparse.ArgumentParser(description="Find the first and last data points for a Sage node.")
    parser.add_argument("vsn", help="VSN of the node (e.g., W077)")
    args = parser.parse_args()

    findNodeLife(args.vsn)


if __name__ == "__main__":
    main()
