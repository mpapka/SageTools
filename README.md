# Sage Beehive Data Toolset

A comprehensive suite of Python utilities for discovering, extracting, and visualizing data from the [Sage Beehive](https://sagecontinuum.org/) platform.

## Features

- **Discovery**: List all nodes, their locations, and their active lifetimes.
- **Diagnostics**: Verify connectivity and discover available sensors/metrics per node.
- **Robust Extraction**: Batch-query years of data with automatic checkpoints and resume support.
- **Visualization**: High-quality plots with gap detection, rolling averages, and custom styling.

---

## Installation

1. **Setup Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 1. Discovery & Exploration

### List All Nodes
Find every node known to Beehive, including GPS coordinates and complete activity history.
```bash
# Normal run (will resume from checkpoint if interrupted)
python listNodes.py

# Start fresh, ignoring any checkpoint
python listNodes.py --reset
```

**Features:**
- **Rich Colorful Output**: Beautiful terminal tables with color-coded information
- **Smart Sorting**: Nodes sorted by installation date (oldest first, newest at bottom)
- **Interactive Export**: Prompts to save CSV with customizable filename
- **Comprehensive Data**: VSN, GPS coordinates, first/last seen dates, and activity periods
- **Detailed Progress**: Shows "Week X of Y" with current date and time remaining
- **Resumable**: Automatically checkpoints every 50 weeks - can be interrupted and resumed
- **Fast Restart**: Run again to continue from where it stopped (no duplicate work)

*Default output: `nodeRegistry.csv` (customizable via interactive prompt).*

**Note**: The activity scanning phase can take a long time (scanning 7+ years of data week-by-week). The script saves checkpoints to `.listNodes.checkpoint` every 50 weeks, so you can safely stop (Ctrl+C) and resume later.

### Find Node Lifetime
Pinpoint the exact first and last seen timestamps for a specific node to plan full-life extraction.
```bash
python nodeLife.py W077
```

### Discover Available Metrics
See exactly what sensors are reporting data on a specific node right now.
```bash
python listMetrics.py
```

### Connectivity Test
Quickly verify if the Beehive API is responsive.
```bash
python quickTest.py
```

### Visualize Node Lifetimes
Create a timeline "tapestry" showing when nodes were active.
```bash
# Plot all nodes from registry
python plotNodeLifetimes.py nodeRegistry.csv

# Save to file
python plotNodeLifetimes.py nodeRegistry.csv --output=timeline.png

# Filter by prefix (e.g., only W08 nodes)
python plotNodeLifetimes.py nodeRegistry.csv --prefix=W08

# Only nodes with GPS coordinates
python plotNodeLifetimes.py nodeRegistry.csv --onlyWithLocation

# Nodes active for at least 365 days
python plotNodeLifetimes.py nodeRegistry.csv --minDays=365
```
- **Visual Timeline**: Horizontal bars showing each node's active periods
- **Color Coded**: Nodes grouped by VSN prefix (W, H, D, V, X)
- **Filtering**: By prefix, location, or minimum lifespan

---

## 2. Data Extraction

### Basic Query (`beehiveQuery.py`)
Best for quick, small data snapshots.
```bash
python beehiveQuery.py --name=env.temperature --vsn=W077 --start=-1h
```

### Resumable Batch Query (`batchQuery.py`)
Recommended for large datasets (weeks/years) or overcoming `500 Internal Server Errors`.
```bash
python batchQuery.py --name=env.temperature --vsn=W077 --start=-1y --chunkSize=1d
```
- **Checkpoints**: Automatically saves progress to `.<filename>.checkpoint`.
- **Auto-Resume**: Rerunning the command will pick up from the last successful chunk.
- **Reset**: Use `--reset` to ignore checkpoints and start fresh.

### Regional Data Collection (`beeHivePro.py`)
Advanced tool for extracting data from entire geographic regions.
```bash
# Sync the node registry with GPS coordinates
python beeHivePro.py sync

# Fetch temperature data for all nodes in a region
python beeHivePro.py region "Chicago" --metric=env.temperature --start=-7d

# Works with any location name (uses OpenStreetMap lookup)
python beeHivePro.py region "Illinois" --metric=env.humidity --start=-30d

# Inverse queries (nodes outside a region)
python beeHivePro.py region "Outside USA" --metric=env.temperature --start=-1d
```
- **Smart Geolocation**: Automatically looks up region boundaries via OpenStreetMap
- **Batch Processing**: Fetches data from all nodes in the region automatically
- **Cached Regions**: Saves region boundaries to `regions.json` for faster reuse
- **GPS Integration**: Uses both metadata GPS and sys.gps.lat/lon for accurate positioning

---

## 3. Visualization

### Plot Temperature (`plotTemperature.py`)
Creates a high-quality visualization of your extracted CSV data.
```bash
# View plot window
python plotTemperature.py temperature_data.csv

# Save to file
python plotTemperature.py temperature_data.csv --output=myPlot.png
```
- **Styling**: Raw data as 1-pixel blue dots (75% transparent) with a red 1-hour rolling average line.
- **Gap Detection**: Automatically breaks lines where data is missing (no misleading straight lines).
- **Date Formatting**: X-axis formatted as `MMM YYYY`.

### Compare Multiple Datasets (`plotComparison.py`)
Plot multiple CSV files on a single graph for side-by-side comparison.
```bash
# Compare multiple nodes
python plotComparison.py node1_temp.csv node2_temp.csv node3_temp.csv

# Save to file with custom title
python plotComparison.py *.csv --output=comparison.pdf --title="Multi-Node Analysis"

# Adjust rolling average window
python plotComparison.py *.csv --rolling=1d
```
- **Auto-coloring**: Each dataset gets a distinct color from the matplotlib cycle
- **Dual layers**: Transparent raw data dots + solid rolling average line per dataset
- **Flexible input**: Accepts any number of CSV files

---

## Configuration & Parameters

- `--name`: Metric name (e.g., `env.temperature`, `env.humidity`, `sys.uptime`).
- `--vsn`: Virtual Site Name (e.g., `W077`).
- `--start`: Supports relative (`-1h`, `-30d`, `-1y`) or absolute ISO timestamps.
- `--chunkSize`: (Batch only) Time window per request (`1h`, `6h`, `1d`).

---

### Heartbeat Tapestry (Activity Map)

To see a detailed "barcode" of exactly when nodes were online/offline:
```bash
python nodeHeartbeat.py --binSize=1w --output=heartbeat.pdf
```
- **`--binSize`**: Resolution of the activity check (e.g., `1d` for daily, `1w` for weekly).
- **Gaps**: Physical white space in the tapestry indicates periods where the node produced no data.
- **Color**: Nodes are grouped and colored by their VSN prefix.

---

## 4. Specialized Collection

### Chicago Data Collection (`collectChicagoData.py`)
A convenience script to extract full historical **temperature records** for 7 key Chicago-area nodes.
```bash
python collectChicagoData.py
```
- **Nodes**: W08D, W08E, W01B, W01C, W076, W05C, W05E
- **Metric**: `env.temperature` (hardcoded)
- **Automatic**: Handles correct start dates and 7-day chunk optimization
- **Output**: Creates `chicago_temp_{VSN}.csv` for each node

**Note**: This script only collects temperature data. For other metrics, use `batchQuery.py` or `beeHivePro.py` directly.

### Enhanced City-Wide Comparison (`plotChicagoComparison.py`)
High-fidelity visualization of all Chicago nodes together.
```bash
python plotChicagoComparison.py chicago_temp_*.csv --output=chicago_final_comparison.pdf
```
- **Fidelity**: Combines `0.005` alpha "smoke" dots with solid, gap-aware rolling average lines
- **Node Differentiation**: Each node is assigned a distinct high-contrast color
- **Scale**: Fixed `[-50, 125]` range for scientific consistency across all data sources

### Hardware-Validated Comparison (`plotChicagoValidated.py`)
Creates temperature plots with strict sensor validation to exclude faulty hardware.
```bash
python plotChicagoValidated.py chicago_temp_*.csv --output=chicago_validated.png

# Custom rolling window
python plotChicagoValidated.py chicago_temp_*.csv --rolling=2h
```
- **Hardware Validation**: Automatically detects and excludes sensors with:
  - Extreme failure values (< -45°F or > 150°F)
  - Internal CPU heating bias (> 125°F ambient threshold)
- **Per-Sensor Analysis**: Validates each sensor/host combination independently
- **Clean Output**: Only plots sensors with valid ambient temperature profiles
- **Focused Range**: Y-axis limited to realistic ambient range (-40°F to 110°F)

### City-Wide Statistical Analysis (`chicagoAnalysis.py`)

To calculate historical records (Min/Max/Avg) across all Chicago nodes:
```bash
python chicagoAnalysis.py
```
- **Memory Efficient**: Uses chunked processing to handle the 10GB+ CSV files safely.
- **Summary Table**: Provides a side-by-side comparison of temperature extremes and record counts for each neighborhood.

### Data Maintenance & Repair (`fixCsvFormat.py`)
If you encounter "Error tokenizing data" (usually due to Beehive changing column formats mid-stream), use this to standardize the file:
```bash
python fixCsvFormat.py chicago_temp_W01B.csv
```
- **Unified Header**: Identifies every possible column across the entire history and rewrites the file with a consistent, standard structure
- **Safety**: Creates a new `_fixed.csv` file, preserving your original data until you choose to replace it

### Sensor Quality Audit (`sensorAudit.py`)
Analyze sensor reliability and detect hardware issues across Chicago datasets.
```bash
python sensorAudit.py
```
- **Per-Sensor Analysis**: Reports statistics for each sensor/host combination separately
- **Quality Metrics**: Min/Max temperatures, record counts, and failure rates
- **Automatic Detection**: Identifies sensors with impossible values or internal heating
- **Memory Efficient**: Processes large (10GB+) CSV files in chunks
- **Rich Output**: Color-coded table showing reliability status (✅ GOOD, ⚠️ FAIL, 🔥 HEATED)

**Note**: Automatically finds and processes all `chicago_temp_*.csv` files in the current directory.

### Performance Tuning (`tuneBatch.py`)
Benchmark different chunk sizes to find optimal extraction performance.
```bash
python tuneBatch.py
```
- **Benchmarks**: Tests chunk sizes from 1 hour to 7 days
- **Performance Metrics**: Rows fetched, time elapsed, and throughput (rows/sec)
- **Recommendations**: Suggests the optimal chunk size for maximum throughput
- **Error Detection**: Identifies which chunk sizes trigger 500 errors

**Use this before large batch extractions** to determine the best `--chunkSize` parameter for your target node.

---

## API Documentation
For deeper technical details, see:
- [Sage Data Client (GitHub)](https://github.com/waggle-sensor/sage-data-client)
- [Sage Continuum Docs](https://sagecontinuum.org/docs/about/overview)