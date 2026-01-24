#!/bin/bash
# Stop all camera SSH tunnels
# Usage: ./stopTunnels.sh

echo "Looking for camera tunnel processes..."

# Find SSH processes related to beekeeper/sagecontinuum tunnels
pids=$(ps aux | grep -E "ssh.*beekeeper|ssh.*sagecontinuum|ssh.*connect-to-node" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "No tunnel processes found."
else
    echo "Found tunnel processes:"
    ps aux | grep -E "ssh.*beekeeper|ssh.*sagecontinuum|ssh.*connect-to-node" | grep -v grep
    echo ""
    echo "Killing processes: $pids"
    echo "$pids" | xargs kill 2>/dev/null
    echo "Done."
fi
