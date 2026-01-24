# Beehive Discovery API

Module: `sage.beehive.discovery`

## listNodes

Discover all nodes in the Sage Beehive network.

### Functions

#### `listAllNodes(outputFile: str = "nodeRegistry.csv") -> pd.DataFrame`

Scan the Beehive for all available nodes and save to CSV.

**Parameters**:
- `outputFile` (str): Path to output CSV file. Default: `"nodeRegistry.csv"`

**Returns**:
- `pd.DataFrame`: DataFrame with columns:
  - `vsn`: Node identifier (e.g., "W01B")
  - `lat`: Latitude (if GPS available)
  - `lon`: Longitude (if GPS available)
  - `firstSeen`: First data point timestamp
  - `lastSeen`: Last data point timestamp
  - `activePeriods`: JSON list of active week periods

**Example**:
```python
from sage.beehive.discovery.listNodes import listAllNodes

df = listAllNodes("nodes.csv")
print(f"Found {len(df)} nodes")
```

#### `loadCheckpoint(checkpointPath: str) -> dict | None`

Load checkpoint from previous scan.

#### `saveCheckpoint(checkpointPath: str, data: dict) -> bool`

Save checkpoint for resume capability.

### CLI Usage

```bash
sage-list-nodes [--output=nodeRegistry.csv]
```

---

## listMetrics

List available metrics for a specific node.

### Functions

#### `listMetrics(vsn: str, start: str = "-24h") -> list[dict]`

Query available metrics for a node.

**Parameters**:
- `vsn` (str): Node identifier (e.g., "W077")
- `start` (str): Time range start. Default: `"-24h"`

**Returns**:
- `list[dict]`: List of metric information:
  - `name`: Metric name (e.g., "env.temperature")
  - `count`: Number of data points
  - `sensors`: List of sensors reporting this metric

**Example**:
```python
from sage.beehive.discovery.listMetrics import listMetrics

metrics = listMetrics("W077")
for m in metrics:
    print(f"{m['name']}: {m['count']} points")
```

### CLI Usage

```bash
sage-list-metrics W077 [--start=-24h]
```

---

## nodeLife

Find the first and last data points for a node.

### Functions

#### `findNodeLife(vsn: str) -> dict`

Determine when a node was first and last active.

**Parameters**:
- `vsn` (str): Node identifier

**Returns**:
- `dict`:
  - `vsn`: Node identifier
  - `firstSeen`: Timestamp of first data point
  - `lastSeen`: Timestamp of last data point
  - `duration`: Active duration string

**Example**:
```python
from sage.beehive.discovery.nodeLife import findNodeLife

life = findNodeLife("W077")
print(f"Active from {life['firstSeen']} to {life['lastSeen']}")
```

### CLI Usage

```bash
sage-node-life W077
```
