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
Find every node known to Beehive, including GPS coordinates and total lifespan.
```bash
python listNodes.py
```
*Outputs `beehiveNodesRegistry.csv`.*

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

### Chicago Data Collection
A convenience script is provided to extract the full historical temperature records for key Chicago-area nodes (`W08D`, `W08E`, `W01B`, `W01C`).
```bash
python collectChicagoData.py
```
This automatically handles the correct start dates and batches the requests for you.

### Enhanced City-Wide Comparison

For high-fidelity visualization of all Chicago nodes together:
```bash
python plotChicagoComparison.py chicago_temp_*.csv --output=chicago_final_comparison.pdf
```
- **Fidelity**: Combines `0.005` alpha "smoke" dots with solid, gap-aware rolling average lines.
- **Node Differentiation**: Each node is assigned a distinct high-contrast color.
- **Scale**: Fixed `[-50, 125]` range for scientific consistency across all data sources.

### City-Wide Statistical Analysis

To calculate historical records (Min/Max/Avg) across all Chicago nodes:
```bash
python chicagoAnalysis.py
```
- **Memory Efficient**: Uses chunked processing to handle the 10GB+ CSV files safely.
- **Summary Table**: Provides a side-by-side comparison of temperature extremes and record counts for each neighborhood.

### Data Maintenance & Repair

If you encounter "Error tokenizing data" (usually due to Beehive changing column formats mid-stream), use `fixCsvFormat.py` to standardize the file:
```bash
python fixCsvFormat.py chicago_temp_W01B.csv
```
- **Unified Header**: Identifies every possible column across the entire history and rewrites the file with a consistent, standard structure.
- **Safety**: Creates a new `_fixed.csv` file, preserving your original data until you choose to replace it.

---

## API Documentation
For deeper technical details, see:
- [Sage Data Client (GitHub)](https://github.com/waggle-sensor/sage-data-client)
- [Sage Continuum Docs](https://sagecontinuum.org/docs/about/overview)