# SageTools

A unified toolkit for working with the Sage Beehive sensor network and Sage Continuum cameras.

**Documentation**: See the [docs/](docs/) directory for detailed guides and API reference.

## Features

### Beehive Data Tools
- **Discovery**: Find nodes, list metrics, discover node lifetimes
- **Extraction**: Query data with adaptive batching and resume support
- **Analysis**: Temperature statistics, sensor auditing, batch tuning
- **Visualization**: Time-series plots, comparisons, lifetime tapestries

### Camera Tools
- **Configuration**: Multi-camera support (AXIS, Hanwha, Mobotix)
- **Connection Testing**: TCP and HTTP connectivity verification
- **Frame Capture**: Single snapshot capture
- **Timelapse**: Automated capture with dashboard display

## Installation

```bash
# Clone the repository
git clone https://github.com/sagecontinuum/SageTools.git
cd SageTools

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Or install with development dependencies (for testing)
pip install -e ".[dev]"
```

## Project Structure

```
SageTools/
├── sage/                    # Main package
│   ├── beehive/            # Beehive data tools
│   │   ├── discovery/      # Node discovery (listNodes, listMetrics, nodeLife)
│   │   ├── extraction/     # Data extraction (query, batchQuery, regionalQuery)
│   │   ├── analysis/       # Data analysis (statistics, sensorAudit, tuneBatch)
│   │   └── visualization/  # Plotting (plotTemperature, plotComparison, etc.)
│   ├── cameras/            # Camera tools
│   │   ├── config.py       # Camera configuration and URL generation
│   │   ├── connection.py   # Connection testing
│   │   ├── captureFrame.py # Single frame capture
│   │   └── captureTimelapse.py  # Timelapse with dashboard
│   └── common/             # Shared utilities
│       ├── checkpoints.py  # Save/load/resume logic
│       ├── regions.py      # Geographic region lookup
│       └── csvUtils.py     # CSV handling utilities
├── scripts/
│   ├── tunnels/            # SSH tunnel management scripts
│   └── examples/           # Example usage scripts
├── tests/                  # Test suite
├── config/                 # Configuration files
├── data/                   # Data directory (gitignored)
├── setup.py
└── requirements.txt
```

## Quick Start

### Beehive Data

```bash
# Test connectivity
python -m sage.beehive.discovery.listMetrics W077

# List all nodes with activity history
python -m sage.beehive.discovery.listNodes

# Find node lifetime
python -m sage.beehive.discovery.nodeLife W077

# Simple data query
python -m sage.beehive.extraction.query --name=env.temperature --vsn=W01B --start=-1h

# Batch query with resume support (for large datasets)
python -m sage.beehive.extraction.batchQuery --name=env.temperature --vsn=W01B --start=2024-01-01 --chunkSize=7d

# Regional data collection
python -m sage.beehive.extraction.regionalQuery region "Chicago" --metric=env.temperature --start=-7d

# Analyze collected data
python -m sage.beehive.analysis.statistics

# Plot temperature data
python -m sage.beehive.visualization.plotTemperature data.csv --output=plot.png

# Compare multiple datasets
python -m sage.beehive.visualization.plotComparison file1.csv file2.csv --output=comparison.png
```

### Cameras

```bash
# Start SSH tunnels (in separate terminal)
./scripts/tunnels/startTunnels.sh V039

# Test camera connectivity
python -m sage.cameras.connection --tunnel

# List available cameras
python -m sage.cameras.captureFrame --list

# Capture single frames
python -m sage.cameras.captureFrame --output=./frames

# Capture timelapse with dashboard
python -m sage.cameras.captureTimelapse --fps=1 --duration=3600 --output=./timelapse

# Capture timelapse (simple mode, no dashboard)
python -m sage.cameras.captureTimelapse --fps=1 --duration=60 --simple
```

## CLI Commands

After installation with `pip install -e .`, these commands are available:

### Beehive Discovery
| Command | Description |
|---------|-------------|
| `sage-list-nodes` | Discover all Beehive nodes with activity history |
| `sage-list-metrics` | List available metrics for a node |
| `sage-node-life` | Find first/last data points for a node |

### Beehive Extraction
| Command | Description |
|---------|-------------|
| `sage-query` | Simple one-shot data query |
| `sage-batch-query` | Batch query with checkpoints and resume |
| `sage-regional` | Region-based multi-node extraction |

### Beehive Analysis
| Command | Description |
|---------|-------------|
| `sage-statistics` | Analyze temperature data files |
| `sage-sensor-audit` | Audit sensor quality and reliability |
| `sage-tune-batch` | Benchmark optimal batch sizes |

### Beehive Visualization
| Command | Description |
|---------|-------------|
| `sage-plot-temp` | Plot temperature time-series |
| `sage-plot-compare` | Compare multiple datasets |
| `sage-plot-lifetimes` | Visualize node lifetimes |
| `sage-plot-heartbeat` | Node activity heartbeat tapestry |

### Cameras
| Command | Description |
|---------|-------------|
| `sage-camera-test` | Test camera connectivity |
| `sage-capture-frame` | Capture single frames |
| `sage-timelapse` | Capture timelapse with dashboard |

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/beehive/test_extraction.py -v

# Run with coverage
pytest tests/ --cov=sage --cov-report=html
```

## Configuration

### Regions

Geographic regions are configured in `config/regions.json`. New regions can be added manually or discovered automatically via OpenStreetMap.

```json
{
    "chicago": {
        "lat": [41.6445, 42.0230],
        "lon": [-87.9401, -87.5241]
    }
}
```

### Cameras

Camera configuration is in `sage/cameras/config.py`. Set `TUNNEL_MODE = True` when using SSH tunnels.

## Dependencies

- `sage-data-client` - Beehive data access
- `pandas` - Data processing
- `matplotlib` - Visualization
- `rich` - CLI interface
- `requests` - HTTP requests
- `python-dateutil` - Date parsing

## Documentation

- **[Getting Started](docs/gettingStarted.md)** - Installation and first steps
- **[Beehive Guide](docs/beehive.md)** - Working with sensor data
- **[Camera Guide](docs/cameras.md)** - Camera setup and capture
- **[API Reference](docs/api/)** - Module documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## External Resources

- [Sage Data Client (GitHub)](https://github.com/waggle-sensor/sage-data-client) - Python client for Beehive API
- [Sage Continuum Docs](https://sagecontinuum.org/docs/about/overview) - Official Sage documentation
- [Waggle Sensor Platform](https://wa8.gl/) - Edge computing platform
