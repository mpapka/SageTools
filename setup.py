#!/usr/bin/env python3
"""
Setup script for SageTools package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    longDescription = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="SageTools",
    version="1.0.0",
    author="Sage Continuum",
    description="A unified toolkit for Sage Beehive data and Sage Continuum cameras",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    url="https://github.com/sagecontinuum/SageTools",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "scripts.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Beehive Discovery
            "sage-list-nodes=sage.beehive.discovery.listNodes:main",
            "sage-list-metrics=sage.beehive.discovery.listMetrics:main",
            "sage-node-life=sage.beehive.discovery.nodeLife:main",
            # Beehive Extraction
            "sage-query=sage.beehive.extraction.query:main",
            "sage-batch-query=sage.beehive.extraction.batchQuery:main",
            "sage-regional=sage.beehive.extraction.regionalQuery:main",
            # Beehive Analysis
            "sage-statistics=sage.beehive.analysis.statistics:main",
            "sage-sensor-audit=sage.beehive.analysis.sensorAudit:main",
            "sage-tune-batch=sage.beehive.analysis.tuneBatch:main",
            # Beehive Visualization
            "sage-plot-temp=sage.beehive.visualization.plotTemperature:main",
            "sage-plot-compare=sage.beehive.visualization.plotComparison:main",
            "sage-plot-lifetimes=sage.beehive.visualization.plotLifetimes:main",
            "sage-plot-heartbeat=sage.beehive.visualization.plotHeartbeat:main",
            # Cameras
            "sage-camera-test=sage.cameras.connection:main",
            "sage-capture-frame=sage.cameras.captureFrame:main",
            "sage-timelapse=sage.cameras.captureTimelapse:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sage": ["config/*.json"],
    },
)
