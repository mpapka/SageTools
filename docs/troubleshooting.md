# Troubleshooting Guide

Common issues and solutions for SageTools.

## Installation Issues

### "No module named 'sage_data_client'"

**Problem**: The Beehive data client isn't installed.

**Solution**:
```bash
pip install sage-data-client
# Or reinstall the package
pip install -e .
```

### "Command not found: sage-list-nodes"

**Problem**: CLI entry points not installed.

**Solution**:
```bash
# Ensure you installed in editable mode
pip install -e .

# Check installation
pip show SageTools
```

### Import Errors After Installation

**Problem**: Python can't find the sage module.

**Solution**:
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall
pip uninstall SageTools
pip install -e .
```

## Beehive Data Issues

### "No data returned" from Query

**Possible causes**:

1. **Node doesn't exist**: Check VSN with `sage-list-nodes`
2. **Metric not available**: Check with `sage-list-metrics <VSN>`
3. **Wrong time range**: Node may not have been active during that period
4. **Network issue**: Test with `sage-list-metrics W077`

**Debug steps**:
```bash
# Verify node exists
sage-list-nodes | grep W01B

# Check what metrics are available
sage-list-metrics W01B

# Check node's active period
sage-node-life W01B

# Try a known-good query
sage-query --name=sys.uptime --vsn=W077 --start=-1h
```

### Query Takes Too Long

**Problem**: Large date range queries are slow or timeout.

**Solution**: Use batch query mode:
```bash
# Instead of this (slow):
sage-query --name=env.temperature --vsn=W01B --start=2024-01-01

# Use this (fast, resumable):
sage-batch-query --name=env.temperature --vsn=W01B --start=2024-01-01 --chunkSize=7d
```

### "Checkpoint file corrupted"

**Problem**: Interrupted query left invalid checkpoint.

**Solution**:
```bash
# Remove the checkpoint file
rm output_file.csv.checkpoint

# Or remove all checkpoints
rm *.checkpoint
```

### CSV Has Inconsistent Columns

**Problem**: Data from different time periods has different columns.

**Solution**: Use the CSV fixer:
```python
from sage.common.csvUtils import fixCsv

fixCsv("problematic_file.csv")
# Creates: problematic_file_fixed.csv
```

### Region Not Found

**Problem**: Regional query can't find the specified region.

**Solution**:
```bash
# Check available regions
python -c "from sage.common.regions import RegionManager; rm = RegionManager(); print(rm.listRegions())"

# Add a custom region to config/regions.json:
{
    "myCity": {
        "lat": [40.0, 41.0],
        "lon": [-75.0, -74.0]
    }
}
```

## Camera Issues

### "Connection refused"

**Possible causes**:

1. **SSH tunnel not running**
2. **Wrong port number**
3. **Camera offline**

**Debug steps**:
```bash
# Check if tunnels are active
./scripts/tunnels/listTunnels.sh

# Test the port directly
nc -zv localhost 8001

# Restart tunnels
./scripts/tunnels/stopTunnels.sh
./scripts/tunnels/startTunnels.sh V039
```

### "401 Unauthorized"

**Problem**: Camera rejecting credentials.

**Solutions**:

1. **Check credentials** in `sage/cameras/config.py`
2. **Verify authentication type**: Most cameras use HTTP Digest Auth
3. **Test in browser**: Visit `http://localhost:8001` while tunnel is active

### "Timeout" During Capture

**Possible causes**:

1. **Network congestion**
2. **Camera overloaded**
3. **Tunnel dropped**

**Solutions**:
```bash
# Reduce capture rate for timelapse
sage-timelapse --fps=0.5 --duration=3600

# Test connectivity first
sage-camera-test --tunnel

# Check and restart tunnel
./scripts/tunnels/stopTunnels.sh
./scripts/tunnels/startTunnels.sh V039
```

### SSH Tunnel Drops Frequently

**Problem**: Long-running captures fail due to tunnel disconnection.

**Solution**: Add keep-alive to SSH config (`~/.ssh/config`):
```
Host *.sagecontinuum.org
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

### Images Are Black or Corrupted

**Possible causes**:

1. **Camera lens cap on** (physical issue)
2. **Exposure settings wrong**
3. **Incomplete HTTP response**

**Debug**:
```bash
# Test with curl to see raw response
curl -v --digest -u username:password http://localhost:8001/axis-cgi/jpg/image.cgi

# Check image file
file captured_image.jpg
```

### Wrong Camera URL Pattern

**Problem**: Different camera models use different URL patterns.

**Solution**: Check camera type in config matches actual hardware:

| Type | Expected URL Pattern |
|------|---------------------|
| AXIS | `/axis-cgi/jpg/image.cgi` |
| Hanwha | `/stw-cgi/image.cgi?msubmenu=jpg` |
| Mobotix | `/cgi-bin/image.jpg` |

## Test Failures

### Tests Fail with "No module named 'sage_data_client'"

**Problem**: Test suite can't mock the module.

**Solution**: This should be handled automatically by `tests/conftest.py`. If not:
```bash
# Install the dependency
pip install sage-data-client

# Or run with mock (already in conftest.py)
pytest tests/ -v
```

### "Fixture not found" Errors

**Problem**: Test can't find pytest fixtures.

**Solution**:
```bash
# Make sure conftest.py exists
ls tests/conftest.py

# Run from project root
cd /path/to/SageTools
pytest tests/ -v
```

## Performance Issues

### High Memory Usage During Large Queries

**Problem**: Loading large CSV files exhausts memory.

**Solutions**:
```python
import pandas as pd

# Read in chunks
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process(chunk)

# Or use specific columns
df = pd.read_csv('large_file.csv', usecols=['timestamp', 'value'])
```

### Slow Plot Generation

**Problem**: Plotting millions of points is slow.

**Solution**: Resample data first:
```bash
sage-plot-temp large_data.csv --resample=1h --output=plot.png
```

Or in Python:
```python
df = df.set_index('timestamp').resample('1h').mean()
```

## Getting More Help

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Versions

```bash
pip show SageTools sage-data-client pandas
python --version
```

### Report an Issue

When reporting issues, include:
1. Command that failed
2. Full error message
3. Python version (`python --version`)
4. Package versions (`pip freeze`)
5. Operating system

Open issues at: https://github.com/sagecontinuum/SageTools/issues
