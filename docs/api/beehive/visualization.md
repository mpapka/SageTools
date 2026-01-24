# Beehive Visualization API

Module: `sage.beehive.visualization`

## plotTemperature

Create time-series temperature plots.

### Functions

#### `plotTemperature(filepath: str, output: str = None, **kwargs) -> bool`

Generate a temperature time-series plot.

**Parameters**:
- `filepath` (str): Path to CSV data file
- `output` (str, optional): Output image path. Default: shows interactive plot
- `**kwargs`:
  - `title` (str): Plot title
  - `resample` (str): Resample interval (e.g., "1h", "1d")
  - `fahrenheit` (bool): Convert to Fahrenheit
  - `figsize` (tuple): Figure size (width, height)
  - `dpi` (int): Output resolution

**Returns**:
- `bool`: True if successful

**Example**:
```python
from sage.beehive.visualization.plotTemperature import plotTemperature

plotTemperature(
    "temperature_data.csv",
    output="temp_plot.png",
    title="Chicago Temperature",
    resample="1h",
    figsize=(12, 6)
)
```

### CLI Usage

```bash
sage-plot-temp data.csv \
    --output=plot.png \
    --title="Temperature Data" \
    --resample=1h \
    --fahrenheit
```

---

## plotComparison

Compare multiple datasets on a single plot.

### Functions

#### `plotComparison(filepaths: list[str], output: str = None, **kwargs) -> bool`

Generate a comparison plot of multiple datasets.

**Parameters**:
- `filepaths` (list[str]): List of CSV file paths
- `output` (str, optional): Output image path
- `**kwargs`:
  - `labels` (list[str]): Legend labels for each dataset
  - `title` (str): Plot title
  - `resample` (str): Resample interval
  - `figsize` (tuple): Figure size

**Returns**:
- `bool`: True if successful

**Example**:
```python
from sage.beehive.visualization.plotComparison import plotComparison

plotComparison(
    ["node1.csv", "node2.csv", "node3.csv"],
    output="comparison.png",
    labels=["Downtown", "Airport", "Lakefront"],
    title="Chicago Temperature Comparison"
)
```

### CLI Usage

```bash
sage-plot-compare node1.csv node2.csv node3.csv \
    --output=comparison.png \
    --labels="Downtown,Airport,Lakefront"
```

---

## plotLifetimes

Visualize node activity over time as a tapestry.

### Functions

#### `plotLifetimes(registryFile: str, output: str = None, **kwargs) -> bool`

Create a node lifetime visualization.

**Parameters**:
- `registryFile` (str): Path to node registry CSV
- `output` (str, optional): Output image path
- `**kwargs`:
  - `prefix` (str): Filter by VSN prefix (e.g., "W")
  - `region` (str): Filter by region
  - `sortBy` (str): Sort order ("firstSeen", "lastSeen", "vsn")
  - `figsize` (tuple): Figure size

**Returns**:
- `bool`: True if successful

**Example**:
```python
from sage.beehive.visualization.plotLifetimes import plotLifetimes

plotLifetimes(
    "nodeRegistry.csv",
    output="lifetimes.png",
    prefix="W",
    sortBy="firstSeen"
)
```

### CLI Usage

```bash
sage-plot-lifetimes nodeRegistry.csv \
    --output=lifetimes.png \
    --prefix=W \
    --sortBy=firstSeen
```

---

## plotHeartbeat

Create node activity heartbeat visualization.

### Functions

#### `plotHeartbeat(registryFile: str, output: str = None, **kwargs) -> bool`

Generate a heartbeat-style activity visualization.

**Parameters**:
- `registryFile` (str): Path to node registry CSV
- `output` (str, optional): Output image path
- `**kwargs`:
  - `resolution` (str): Time resolution ("week", "day", "hour")
  - `colormap` (str): Matplotlib colormap name
  - `figsize` (tuple): Figure size

**Returns**:
- `bool`: True if successful

**Example**:
```python
from sage.beehive.visualization.plotHeartbeat import plotHeartbeat

plotHeartbeat(
    "nodeRegistry.csv",
    output="heartbeat.png",
    resolution="week"
)
```

### CLI Usage

```bash
sage-plot-heartbeat nodeRegistry.csv \
    --output=heartbeat.png \
    --resolution=week
```
