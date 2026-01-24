# Common Utilities API

Module: `sage.common`

## checkpoints

Save and restore state for resumable operations.

### Functions

#### `getCheckpointPath(outputFile: str) -> str`

Generate checkpoint file path from output file.

**Parameters**:
- `outputFile` (str): Path to output file

**Returns**:
- `str`: Checkpoint file path (adds `.checkpoint` extension)

**Example**:
```python
from sage.common.checkpoints import getCheckpointPath

path = getCheckpointPath("data/output.csv")
# Returns: "data/output.csv.checkpoint"
```

#### `saveCheckpoint(checkpointPath: str, data: dict, usePickle: bool = False) -> bool`

Save state to checkpoint file.

**Parameters**:
- `checkpointPath` (str): Path to checkpoint file
- `data` (dict): State data to save
- `usePickle` (bool): Use pickle instead of JSON. Default: False

**Returns**:
- `bool`: True if saved successfully

**Example**:
```python
from sage.common.checkpoints import saveCheckpoint

state = {
    "currentChunk": 5,
    "totalChunks": 20,
    "processedRows": 15000
}
saveCheckpoint("query.checkpoint", state)
```

#### `loadCheckpoint(checkpointPath: str) -> dict | None`

Load state from checkpoint file.

**Parameters**:
- `checkpointPath` (str): Path to checkpoint file

**Returns**:
- `dict`: Loaded state data
- `None`: If checkpoint doesn't exist or is corrupted

**Example**:
```python
from sage.common.checkpoints import loadCheckpoint

state = loadCheckpoint("query.checkpoint")
if state:
    print(f"Resuming from chunk {state['currentChunk']}")
```

#### `clearCheckpoint(checkpointPath: str) -> bool`

Delete a checkpoint file.

**Parameters**:
- `checkpointPath` (str): Path to checkpoint file

**Returns**:
- `bool`: True if deleted (or didn't exist)

---

## regions

Geographic region management with OpenStreetMap integration.

### Classes

#### `RegionManager`

Manage geographic regions for node filtering.

**Constructor**:
```python
RegionManager(regionsFile: str = "config/regions.json")
```

**Methods**:

##### `getBbox(query: str) -> dict | None`

Get bounding box for a region.

**Parameters**:
- `query` (str): Region name (e.g., "Chicago") or custom query

**Returns**:
- `dict`: Bounding box with `lat` and `lon` ranges
- `None`: If region not found

**Example**:
```python
from sage.common.regions import RegionManager

rm = RegionManager()

bbox = rm.getBbox("Chicago")
# Returns: {"lat": [41.6445, 42.0230], "lon": [-87.9401, -87.5241]}

# Also works with OpenStreetMap queries
bbox = rm.getBbox("Austin, Texas")
```

##### `addRegion(name: str, latRange: list, lonRange: list) -> bool`

Add a custom region.

**Parameters**:
- `name` (str): Region name
- `latRange` (list): [min_lat, max_lat]
- `lonRange` (list): [min_lon, max_lon]

**Returns**:
- `bool`: True if added successfully

##### `removeRegion(name: str) -> bool`

Remove a region.

**Parameters**:
- `name` (str): Region name

**Returns**:
- `bool`: True if removed

##### `listRegions() -> list[str]`

Get list of defined regions.

**Returns**:
- `list[str]`: Region names

**Example**:
```python
from sage.common.regions import RegionManager

rm = RegionManager()

# Add custom region
rm.addRegion("myArea", [40.0, 41.0], [-75.0, -74.0])

# List all regions
print(rm.listRegions())
# Output: ["chicago", "usa", "myArea"]
```

---

## csvUtils

CSV manipulation and fixing utilities.

### Functions

#### `alignColumns(df: pd.DataFrame, targetColumns: list) -> pd.DataFrame`

Align DataFrame columns to match target.

**Parameters**:
- `df` (pd.DataFrame): Source DataFrame
- `targetColumns` (list): Target column names

**Returns**:
- `pd.DataFrame`: DataFrame with aligned columns

**Behavior**:
- Adds missing columns (filled with NaN)
- Removes extra columns
- Reorders to match target

**Example**:
```python
from sage.common.csvUtils import alignColumns
import pandas as pd

df = pd.DataFrame({'a': [1, 2], 'c': [5, 6]})
target = ['a', 'b', 'c']

aligned = alignColumns(df, target)
# Result has columns: ['a', 'b', 'c']
# Column 'b' is NaN
```

#### `getExistingColumns(filepath: str) -> list | None`

Get column names from existing CSV file.

**Parameters**:
- `filepath` (str): Path to CSV file

**Returns**:
- `list`: Column names
- `None`: If file doesn't exist

#### `fixCsv(inputFile: str, outputFile: str = None, chunkSize: int = 10000) -> bool`

Fix CSV with inconsistent columns.

**Parameters**:
- `inputFile` (str): Path to input CSV
- `outputFile` (str, optional): Output path. Default: `{input}_fixed.csv`
- `chunkSize` (int): Processing chunk size. Default: 10000

**Returns**:
- `bool`: True if fixed successfully

**Example**:
```python
from sage.common.csvUtils import fixCsv

# Creates "data_fixed.csv" with consistent columns
fixCsv("data.csv")

# Custom output path
fixCsv("data.csv", outputFile="clean_data.csv")
```

#### `mergeCsvFiles(inputFiles: list, outputFile: str, dedup: bool = False) -> bool`

Merge multiple CSV files.

**Parameters**:
- `inputFiles` (list): Paths to input files
- `outputFile` (str): Output file path
- `dedup` (bool): Remove duplicate rows. Default: False

**Returns**:
- `bool`: True if merged successfully

**Example**:
```python
from sage.common.csvUtils import mergeCsvFiles

mergeCsvFiles(
    ["data_jan.csv", "data_feb.csv", "data_mar.csv"],
    "data_q1.csv",
    dedup=True
)
```
