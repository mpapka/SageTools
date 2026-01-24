#!/usr/bin/env python3
"""
Quick connectivity test for Sage Beehive.

Tests connectivity to the Sage Beehive platform by querying sys.uptime,
a reliable heartbeat metric.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import sage_data_client
import pandas as pd


def quickTest():
    """Test connectivity with a simple query."""
    print("Testing connectivity with a simple query (sys.uptime)...")
    try:
        # sys.uptime is generally very reliable
        df = sage_data_client.query(
            start="-5m",
            filter={"name": "sys.uptime"}
        )
        if df.empty:
            print("Query succeeded but returned no data.")
        else:
            print(f"Success! Found {len(df)} uptime records.")
            print(df.tail(3))
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    quickTest()
