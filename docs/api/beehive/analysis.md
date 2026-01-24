# Beehive Analysis API

Module: `sage.beehive.analysis`

## statistics

Temperature data statistics and analysis.

### Functions

#### `analyzeFile(filepath: str) -> dict`

Compute statistics for a temperature data file.

**Parameters**:
- `filepath` (str): Path to CSV file

**Returns**:
- `dict`:
  - `count`: Number of data points
  - `mean`: Mean temperature
  - `std`: Standard deviation
  - `min`: Minimum temperature
  - `max`: Maximum temperature
  - `start`: First timestamp
  - `end`: Last timestamp

**Example**:
```python
from sage.beehive.analysis.statistics import analyzeFile

stats = analyzeFile("temperature_data.csv")
print(f"Mean: {stats['mean']:.1f}°C")
print(f"Range: {stats['min']:.1f} - {stats['max']:.1f}°C")
```

#### `celsiusToFahrenheit(celsius: float) -> float`

Convert Celsius to Fahrenheit.

#### `fahrenheitToCelsius(fahrenheit: float) -> float`

Convert Fahrenheit to Celsius.

### CLI Usage

```bash
sage-statistics data.csv [--fahrenheit]
```

---

## sensorAudit

Audit sensor health and data quality.

### Functions

#### `auditFile(filepath: str) -> dict`

Analyze a data file for sensor issues.

**Parameters**:
- `filepath` (str): Path to CSV file

**Returns**:
- `dict`:
  - `totalPoints`: Total data points
  - `gaps`: List of data gaps (missing periods)
  - `stuckValues`: Periods where sensor reported same value
  - `outliers`: Physically impossible values
  - `sensors`: Per-sensor statistics

**Example**:
```python
from sage.beehive.analysis.sensorAudit import auditFile

audit = auditFile("temperature_data.csv")

if audit['gaps']:
    print(f"Found {len(audit['gaps'])} data gaps:")
    for gap in audit['gaps']:
        print(f"  {gap['start']} to {gap['end']}")

if audit['outliers']:
    print(f"Found {len(audit['outliers'])} outliers")
```

#### `detectGaps(df: pd.DataFrame, threshold: str = "1h") -> list[dict]`

Find gaps in time-series data.

#### `detectStuckSensor(df: pd.DataFrame, threshold: int = 10) -> list[dict]`

Find periods where sensor reported identical values.

#### `detectOutliers(df: pd.DataFrame, minTemp: float = -50, maxTemp: float = 60) -> list[dict]`

Find physically impossible temperature values.

### CLI Usage

```bash
sage-sensor-audit data.csv [--threshold=1h] [--minTemp=-50] [--maxTemp=60]
```

---

## tuneBatch

Benchmark and optimize batch query sizes.

### Functions

#### `benchmark(vsn: str, metric: str, chunkSizes: list[str] = None) -> dict`

Test different batch sizes to find optimal configuration.

**Parameters**:
- `vsn` (str): Node identifier
- `metric` (str): Metric name
- `chunkSizes` (list[str], optional): Sizes to test. Default: ["1d", "3d", "7d", "14d"]

**Returns**:
- `dict`:
  - `results`: List of benchmark results per chunk size
  - `optimal`: Recommended chunk size
  - `summary`: Human-readable summary

**Example**:
```python
from sage.beehive.analysis.tuneBatch import benchmark

results = benchmark("W01B", "env.temperature")
print(f"Optimal chunk size: {results['optimal']}")

for r in results['results']:
    print(f"  {r['chunkSize']}: {r['avgTime']:.2f}s per chunk")
```

### CLI Usage

```bash
sage-tune-batch --vsn=W01B --metric=env.temperature [--chunks=1d,3d,7d,14d]
```
