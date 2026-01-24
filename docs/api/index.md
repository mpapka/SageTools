# API Reference

Detailed documentation for SageTools modules.

## Package Structure

```
sage/
├── beehive/           # Beehive sensor data tools
│   ├── discovery/     # Node and metric discovery
│   ├── extraction/    # Data querying and download
│   ├── analysis/      # Data analysis utilities
│   └── visualization/ # Plotting and charts
├── cameras/           # Camera capture tools
└── common/            # Shared utilities
```

## Module Index

### Beehive Discovery
- [listNodes](beehive/discovery.md#listnodes) - Discover all nodes in the network
- [listMetrics](beehive/discovery.md#listmetrics) - List metrics for a specific node
- [nodeLife](beehive/discovery.md#nodelife) - Find node first/last activity

### Beehive Extraction
- [query](beehive/extraction.md#query) - Simple one-shot data queries
- [batchQuery](beehive/extraction.md#batchquery) - Large dataset extraction with checkpoints
- [regionalQuery](beehive/extraction.md#regionalquery) - Geographic region-based queries

### Beehive Analysis
- [statistics](beehive/analysis.md#statistics) - Temperature data statistics
- [sensorAudit](beehive/analysis.md#sensoraudit) - Sensor health auditing
- [tuneBatch](beehive/analysis.md#tunebatch) - Batch size optimization

### Beehive Visualization
- [plotTemperature](beehive/visualization.md#plottemperature) - Time-series plots
- [plotComparison](beehive/visualization.md#plotcomparison) - Multi-dataset comparison
- [plotLifetimes](beehive/visualization.md#plotlifetimes) - Node lifetime tapestry
- [plotHeartbeat](beehive/visualization.md#plotheartbeat) - Activity heartbeat

### Cameras
- [config](cameras.md#config) - Camera configuration and URL generation
- [connection](cameras.md#connection) - Connectivity testing
- [captureFrame](cameras.md#captureframe) - Single frame capture
- [captureTimelapse](cameras.md#capturetimelapse) - Timelapse capture

### Common Utilities
- [checkpoints](common.md#checkpoints) - Save/load/resume state
- [regions](common.md#regions) - Geographic region management
- [csvUtils](common.md#csvutils) - CSV manipulation utilities
