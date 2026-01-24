# Getting Started with SageTools

This guide will help you install SageTools and run your first queries.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- SSH access to Sage nodes (for camera features)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sagecontinuum/SageTools.git
cd SageTools
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install the Package

```bash
# Standard installation
pip install -e .

# With development dependencies (for running tests)
pip install -e ".[dev]"
```

### 4. Verify Installation

```bash
# Check that CLI commands are available
sage-list-nodes --help

# Test Beehive connectivity
python -m sage.beehive.discovery.listMetrics W077
```

## Quick Start Examples

### Query Beehive Data

```bash
# List all available nodes
sage-list-nodes

# Get temperature data from a specific node
sage-query --name=env.temperature --vsn=W01B --start=-1h

# Find when a node was first/last active
sage-node-life W077
```

### Capture Camera Frames

```bash
# First, start SSH tunnels to the node (in a separate terminal)
./scripts/tunnels/startTunnels.sh V039

# Test camera connectivity
sage-camera-test --tunnel

# Capture a single frame from all cameras
sage-capture-frame --output=./frames
```

## Project Structure Overview

```
SageTools/
├── sage/                    # Main Python package
│   ├── beehive/            # Beehive sensor data tools
│   │   ├── discovery/      # Find nodes and metrics
│   │   ├── extraction/     # Query and download data
│   │   ├── analysis/       # Analyze collected data
│   │   └── visualization/  # Create plots and charts
│   ├── cameras/            # Camera capture tools
│   └── common/             # Shared utilities
├── scripts/                # Shell scripts and examples
├── tests/                  # Test suite
├── config/                 # Configuration files
└── docs/                   # Documentation (you are here)
```

## Next Steps

- **[Beehive Guide](beehive.md)** - Learn to query and analyze sensor data
- **[Camera Guide](cameras.md)** - Set up cameras and capture images
- **[API Reference](api/)** - Detailed module documentation
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md) for common issues
- Review the [Sage Continuum Documentation](https://sagecontinuum.org/docs/about/overview)
- Open an issue on [GitHub](https://github.com/sagecontinuum/SageTools/issues)
