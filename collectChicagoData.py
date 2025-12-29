#!/usr/bin/env python3
import subprocess
import os

def runCommand(cmd):
    print(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True)

def collectData():
    # Targeted Chicago area nodes
    nodes = {
        "W08D": "2022-05-27",
        "W08E": "2022-06-13",
        "W01B": "2021-09-14",
        "W01C": "2021-09-14",
        "W076": "2023-06-14",
        "W05C": "2023-06-14",
        "W05E": "2023-09-15"
    }
    
    # We skip W08F as it seemed to have very little data in the probe
    
    for vsn, startDate in nodes.items():
        outputFile = f"chicago_temp_{vsn}.csv"
        print(f"\n--- Starting extraction for {vsn} ---")
        
        # We use a 7-day chunk size for maximum throughput based on benchmarks
        cmd = f"python3 batchQuery.py --name=env.temperature --vsn={vsn} --start={startDate} --chunkSize=7d --output={outputFile}"
        runCommand(cmd)

if __name__ == "__main__":
    collectData()

