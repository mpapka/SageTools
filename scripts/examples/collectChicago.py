#!/usr/bin/env python3
"""
Collect temperature data for Chicago area nodes.

This script extracts temperature data for a set of targeted Chicago nodes
using the batch query functionality.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sage.beehive.extraction.batchQuery import runBatchQuery


def collectData():
    """Collect temperature data for Chicago area nodes."""

    # Targeted Chicago area nodes with their start dates
    nodes = {
        "W08D": "2022-05-27",
        "W08E": "2022-06-13",
        "W01B": "2021-09-14",
        "W01C": "2021-09-14",
        "W076": "2023-06-14",
        "W05C": "2023-06-14",
        "W05E": "2023-09-15"
    }

    for vsn, startDate in nodes.items():
        outputFile = f"chicago_temp_{vsn}.csv"
        print(f"\n--- Starting extraction for {vsn} ---")

        # Use a 7-day chunk size for maximum throughput based on benchmarks
        runBatchQuery(
            name="env.temperature",
            vsn=vsn,
            start=startDate,
            end="now",
            chunkSize="7d",
            output=outputFile
        )


if __name__ == "__main__":
    collectData()
