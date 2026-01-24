# Beehive Data Guide

This guide covers working with sensor data from the Sage Beehive network.

## Overview

The Sage Beehive is a data repository that collects measurements from edge nodes deployed around the world. Each node has sensors that report metrics like temperature, humidity, air quality, and more.

## Understanding the Data Model

### Key Concepts

- **Node (VSN)**: A physical device with sensors (e.g., `W01B`, `W077`)
- **Metric**: A type of measurement (e.g., `env.temperature`, `sys.uptime`)
- **Sensor**: The hardware producing data (e.g., `bme280`, `bme680`)
- **Timestamp**: When the measurement was taken (UTC)

### Common Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `env.temperature` | Air temperature | Celsius |
| `env.relative_humidity` | Relative humidity | % |
| `env.pressure` | Barometric pressure | hPa |
| `env.raingauge.total_acc` | Accumulated rainfall | mm |
| `sys.uptime` | Node uptime | seconds |
| `sys.mem.free` | Free memory | bytes |

## Discovery Tools

### List All Nodes

Scan the Beehive for all available nodes:

```bash
sage-list-nodes

# Output includes:
# - VSN (node identifier)
# - GPS coordinates (if available)
# - First/last seen timestamps
# - Weekly activity pattern
```

The results are saved to `nodeRegistry.csv` for offline use.

### List Metrics for a Node

See what data a specific node provides:

```bash
sage-list-metrics W077

# Shows all metrics reported by node W077
# with sample counts and date ranges
```

### Find Node Lifetime

Determine when a node was active:

```bash
sage-node-life W077

# Returns:
# - First data point timestamp
# - Last data point timestamp
# - Total active duration
```

## Data Extraction

### Simple Query

For quick, one-off queries:

```bash
# Get last hour of temperature data
sage-query --name=env.temperature --vsn=W01B --start=-1h

# Get specific date range
sage-query --name=env.temperature --vsn=W01B \
    --start=2024-01-01 --end=2024-01-02
```

**Output**: CSV file with columns: `timestamp`, `value`, `name`, `meta.vsn`, `meta.sensor`, etc.

### Batch Query (Large Datasets)

For queries spanning weeks or months, use batch mode with automatic checkpointing:

```bash
sage-batch-query \
    --name=env.temperature \
    --vsn=W01B \
    --start=2024-01-01 \
    --end=2024-06-01 \
    --chunkSize=7d \
    --output=temperature_data.csv
```

**Features**:
- Splits query into manageable chunks (default: 7 days)
- Saves progress to checkpoint file (`.checkpoint`)
- Resumes automatically if interrupted
- Shows progress bar with ETA

**Resuming an interrupted query**:
```bash
# Just run the same command again - it will detect the checkpoint
sage-batch-query --name=env.temperature --vsn=W01B --start=2024-01-01
```

### Regional Query

Query all nodes within a geographic region:

```bash
# Query all Chicago nodes
sage-regional region "Chicago" \
    --metric=env.temperature \
    --start=-7d

# Query by custom bounding box
sage-regional bbox 41.8 42.0 -87.9 -87.5 \
    --metric=env.temperature \
    --start=-7d
```

**Regions** are defined in `config/regions.json` or looked up via OpenStreetMap.

## Data Analysis

### Temperature Statistics

Analyze temperature data files:

```bash
sage-statistics temperature_data.csv

# Output:
# - Mean, min, max temperatures
# - Standard deviation
# - Data point count
# - Time range covered
```

### Sensor Audit

Check sensor health and data quality:

```bash
sage-sensor-audit temperature_data.csv

# Detects:
# - Missing data gaps
# - Sensor failures (stuck values)
# - Outliers (physically impossible values)
# - Timestamp anomalies
```

### Batch Size Tuning

Optimize query performance:

```bash
sage-tune-batch --vsn=W01B --metric=env.temperature

# Tests different batch sizes and reports
# optimal chunk size for your queries
```

## Visualization

### Temperature Plot

Create time-series plots:

```bash
sage-plot-temp temperature_data.csv --output=plot.png

# Options:
#   --title "Custom Title"
#   --resample 1h    # Resample to hourly
#   --fahrenheit     # Convert to Fahrenheit
```

### Comparison Plot

Compare multiple datasets:

```bash
sage-plot-compare node1.csv node2.csv node3.csv \
    --output=comparison.png \
    --labels "Node 1,Node 2,Node 3"
```

### Node Lifetime Visualization

Create a tapestry showing when nodes were active:

```bash
sage-plot-lifetimes nodeRegistry.csv --output=lifetimes.png

# Filter options:
#   --prefix W      # Only W-series nodes
#   --region chicago # Only Chicago nodes
```

### Activity Heartbeat

Visualize node activity patterns:

```bash
sage-plot-heartbeat nodeRegistry.csv --output=heartbeat.png
```

## Working with CSV Output

All extraction tools output CSV files compatible with pandas:

```python
import pandas as pd

# Load data
df = pd.read_csv('temperature_data.csv')

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Basic analysis
print(df['value'].describe())

# Plot with matplotlib
df.plot(x='timestamp', y='value')
```

## Tips and Best Practices

### Query Optimization

1. **Start small**: Test queries with `--start=-1h` before requesting large date ranges
2. **Use batch mode**: For queries > 1 week, always use `sage-batch-query`
3. **Specify end dates**: Open-ended queries can be slow

### Data Quality

1. **Check for gaps**: Use `sage-sensor-audit` to identify missing data
2. **Validate values**: Temperature should be -50 to 60 C for most locations
3. **Note timezone**: All timestamps are UTC

### Storage

1. **CSV files can be large**: 1 year of data at 1-minute intervals ~ 500K rows
2. **Use compression**: `gzip temperature_data.csv` for archival
3. **Data directory**: Store files in `data/csv/` (gitignored)

## External Resources

- [sage-data-client Documentation](https://github.com/waggle-sensor/sage-data-client)
- [Beehive Data API](https://sagecontinuum.org/docs/about/architecture)
- [Available Metrics List](https://sagecontinuum.org/docs/about/architecture)
