#!/bin/bash
# List running camera tunnels and their ports
# Usage: ./listTunnels.sh

echo "=== SSH Tunnel Processes ==="
ps aux | grep -E "ssh.*beekeeper|ssh.*sagecontinuum|ssh.*connect-to-node" | grep -v grep

echo ""
echo "=== Ports Listening (8xxx) ==="
lsof -i -P | grep LISTEN | grep -E ":8[0-1][0-9][0-9]" | awk '{print $1, $2, $9}'

echo ""
echo "=== Expected Camera Ports ==="
echo "  8091 - axisPtzApiary"
echo "  8092 - hanwhaPtzApiary"
echo "  8119 - mobotixThermalApiary"
echo "  8149 - hanwhaSkyApiary1"
echo "  8150 - hanwhaSkyApiary2"
echo "  8153 - hanwhaPtzAtmos"
