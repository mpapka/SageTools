"""
Geographic region management for Sage Beehive.

Provides region lookup, caching, and dynamic boundary discovery via OpenStreetMap.
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Optional

from rich.console import Console

console = Console()

# Default configuration file path
DEFAULT_CONFIG_FILE = "config/regions.json"


class RegionManager:
    """
    Manage geographic regions for filtering nodes.

    Supports predefined regions and dynamic lookup via OpenStreetMap Nominatim API.
    Results are cached locally for future use.
    """

    def __init__(self, configFile: str = None):
        """
        Initialize the RegionManager.

        Args:
            configFile: Path to regions.json config file. If None, uses default location.
        """
        if configFile is None:
            # Try to find config file in standard locations
            possiblePaths = [
                DEFAULT_CONFIG_FILE,
                "regions.json",
                os.path.join(os.path.dirname(__file__), "..", "..", "config", "regions.json"),
            ]
            for path in possiblePaths:
                if os.path.exists(path):
                    configFile = path
                    break
            else:
                configFile = DEFAULT_CONFIG_FILE

        self.configFile = configFile
        self.regions = self._load()

    def _load(self) -> dict:
        """Load regions from config file or create defaults."""
        if os.path.exists(self.configFile):
            try:
                with open(self.configFile, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load regions config: {e}[/yellow]")

        # Default starter regions
        defaults = {
            "usa": {"lat": [24.0, 49.0], "lon": [-125.0, -66.0]},
            "chicago": {"lat": [41.6445, 42.0230], "lon": [-87.9401, -87.5241]}
        }
        self._save(defaults)
        return defaults

    def _save(self, data: dict) -> bool:
        """Save regions to config file."""
        try:
            # Create directory if needed
            configDir = os.path.dirname(self.configFile)
            if configDir and not os.path.exists(configDir):
                os.makedirs(configDir, exist_ok=True)

            with open(self.configFile, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save regions config: {e}[/yellow]")
            return False

    def getBbox(self, query: str) -> Optional[dict]:
        """
        Get bounding box for a region query.

        Args:
            query: Region name (e.g., "Chicago", "Illinois", "USA")
                   Can be prefixed with "outside " for inverse matching.

        Returns:
            Dictionary with 'lat' and 'lon' keys, each containing [min, max] values.
            Returns None if region cannot be found.
        """
        queryKey = query.lower().replace(" ", "_")

        # Check cache first
        if queryKey in self.regions:
            return self.regions[queryKey]

        # Dynamic lookup via OpenStreetMap Nominatim
        console.print(f"[yellow]Searching for boundaries of '{query}' online...[/yellow]")
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
            headers = {'User-Agent': 'SageTools/1.0 (Educational Tool)'}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data:
                    bbox = [float(x) for x in data[0]['boundingbox']]
                    # OSM order: [minLat, maxLat, minLon, maxLon]
                    result = {"lat": [bbox[0], bbox[1]], "lon": [bbox[2], bbox[3]]}

                    # Cache result
                    self.regions[queryKey] = result
                    self._save(self.regions)

                    console.print(f"[green]Found region: lat {result['lat']}, lon {result['lon']}[/green]")
                    return result
        except Exception as e:
            console.print(f"[red]Could not find region '{query}': {e}[/red]")

        return None

    def listRegions(self) -> list:
        """
        List all cached region names.

        Returns:
            List of region names
        """
        return list(self.regions.keys())

    def addRegion(self, name: str, latRange: list, lonRange: list) -> bool:
        """
        Manually add a region definition.

        Args:
            name: Region name
            latRange: [minLat, maxLat]
            lonRange: [minLon, maxLon]

        Returns:
            True if added successfully
        """
        key = name.lower().replace(" ", "_")
        self.regions[key] = {"lat": latRange, "lon": lonRange}
        return self._save(self.regions)

    def removeRegion(self, name: str) -> bool:
        """
        Remove a region from the cache.

        Args:
            name: Region name to remove

        Returns:
            True if removed successfully
        """
        key = name.lower().replace(" ", "_")
        if key in self.regions:
            del self.regions[key]
            return self._save(self.regions)
        return False
