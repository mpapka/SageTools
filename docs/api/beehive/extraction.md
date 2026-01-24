# Beehive Extraction API

Module: `sage.beehive.extraction`

## query

Simple one-shot data queries.

### Functions

#### `runQuery(name: str, vsn: str, start: str, end: str = None, output: str = None) -> pd.DataFrame`

Execute a simple Beehive query.

**Parameters**:
- `name` (str): Metric name (e.g., "env.temperature")
- `vsn` (str): Node identifier (e.g., "W01B")
- `start` (str): Start time (ISO format or relative like "-1h")
- `end` (str, optional): End time. Default: now
- `output` (str, optional): Output CSV path

**Returns**:
- `pd.DataFrame`: Query results with columns:
  - `timestamp`: Measurement time (UTC)
  - `value`: Measured value
  - `name`: Metric name
  - `meta.vsn`: Node identifier
  - `meta.sensor`: Sensor name
  - `meta.host`: Host identifier

**Example**:
```python
from sage.beehive.extraction.query import runQuery

df = runQuery(
    name="env.temperature",
    vsn="W01B",
    start="-1h",
    output="temp_data.csv"
)
print(f"Got {len(df)} rows")
```

### CLI Usage

```bash
sage-query --name=env.temperature --vsn=W01B --start=-1h [--end=now] [--output=data.csv]
```

---

## batchQuery

Large dataset extraction with checkpoints and resume support.

### Functions

#### `runBatchQuery(name: str, vsn: str, start: str, end: str = None, chunkSize: str = "7d", output: str = None) -> bool`

Execute a chunked query with automatic checkpointing.

**Parameters**:
- `name` (str): Metric name
- `vsn` (str): Node identifier
- `start` (str): Start time (ISO format)
- `end` (str, optional): End time. Default: now
- `chunkSize` (str): Chunk size (e.g., "7d", "1d", "12h"). Default: "7d"
- `output` (str, optional): Output CSV path

**Returns**:
- `bool`: True if completed successfully

**Example**:
```python
from sage.beehive.extraction.batchQuery import runBatchQuery

success = runBatchQuery(
    name="env.temperature",
    vsn="W01B",
    start="2024-01-01",
    end="2024-06-01",
    chunkSize="7d",
    output="temperature_2024.csv"
)
```

#### `getCheckpointPath(outputFile: str) -> str`

Get checkpoint file path for an output file.

#### `saveCheckpoint(checkpointPath: str, state: dict) -> bool`

Save query progress to checkpoint file.

#### `loadCheckpoint(checkpointPath: str) -> dict | None`

Load checkpoint for resume.

### CLI Usage

```bash
sage-batch-query \
    --name=env.temperature \
    --vsn=W01B \
    --start=2024-01-01 \
    --end=2024-06-01 \
    --chunkSize=7d \
    --output=data.csv
```

---

## regionalQuery

Query data for all nodes within a geographic region.

### Classes

#### `BeeHivePro`

Regional data extraction with caching and parallel queries.

**Constructor**:
```python
BeeHivePro(
    regionsFile: str = "config/regions.json",
    cacheDir: str = "data/cache"
)
```

**Methods**:

##### `getNodesInRegion(region: str) -> list[str]`

Get list of node VSNs within a region.

**Parameters**:
- `region` (str): Region name (e.g., "Chicago") or "bbox:lat1,lat2,lon1,lon2"

**Returns**:
- `list[str]`: List of VSNs

##### `queryRegion(region: str, metric: str, start: str, end: str = None) -> pd.DataFrame`

Query all nodes in a region.

**Parameters**:
- `region` (str): Region name or bounding box
- `metric` (str): Metric name
- `start` (str): Start time
- `end` (str, optional): End time

**Returns**:
- `pd.DataFrame`: Combined data from all nodes

**Example**:
```python
from sage.beehive.extraction.regionalQuery import BeeHivePro

pro = BeeHivePro()

# Get Chicago nodes
nodes = pro.getNodesInRegion("Chicago")
print(f"Found {len(nodes)} nodes in Chicago")

# Query all Chicago temperature data
df = pro.queryRegion("Chicago", "env.temperature", "-7d")
```

### CLI Usage

```bash
# Query by region name
sage-regional region "Chicago" --metric=env.temperature --start=-7d

# Query by bounding box
sage-regional bbox 41.8 42.0 -87.9 -87.5 --metric=env.temperature --start=-7d
```
