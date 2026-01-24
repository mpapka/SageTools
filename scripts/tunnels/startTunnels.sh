#!/bin/bash
# Start SSH tunnels to all cameras through Sage node
# Usage: ./startTunnels.sh [node]
# Example: ./startTunnels.sh V039

NODE="${1:-V039}"
SSH_KEY="${SSH_KEY:-~/.ssh/sageKey}"
BEEKEEPER="waggle@beekeeper.sagecontinuum.org"
BEEKEEPER_PORT=49190

echo "Starting camera tunnels through node $NODE..."
echo "SSH key: $SSH_KEY"
echo ""
echo "Port mappings:"
echo "  axisPtzApiary:        localhost:8091 -> 130.202.23.91:80"
echo "  hanwhaPtzApiary:      localhost:8092 -> 130.202.23.92:80"
echo "  mobotixThermalApiary: localhost:8119 -> 130.202.23.119:80"
echo "  hanwhaSkyApiary1:     localhost:8149 -> 130.202.23.149:80"
echo "  hanwhaSkyApiary2:     localhost:8150 -> 130.202.23.150:80"
echo "  hanwhaPtzAtmos:       localhost:8153 -> 130.202.23.153:80"
echo ""
echo "Starting SSH tunnel (Ctrl+C to stop)..."
echo ""

ssh \
    -i "$SSH_KEY" \
    -N \
    -L 8091:130.202.23.91:80 \
    -L 8092:130.202.23.92:80 \
    -L 8119:130.202.23.119:80 \
    -L 8149:130.202.23.149:80 \
    -L 8150:130.202.23.150:80 \
    -L 8153:130.202.23.153:80 \
    -o ProxyCommand="ssh -i $SSH_KEY -p $BEEKEEPER_PORT $BEEKEEPER connect-to-node $NODE" \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    waggle@localhost
