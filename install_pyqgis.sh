#!/bin/bash

### read in command-line arguments
while [ $# -gt 0 ]; do
    if [[ $1 == "--"* ]]; then
        v="${1/--/}"
        declare "$v"="$2"
        shift
    fi
    shift
done

echo "Installing required Python packages for QGIS"

$python_path -m pip install momepy contextily osmnx==1.6.0
$python_path -m pip install numpy --force-reinstall -v numpy==1.22.4
$python_path -m pip install --upgrade shapely lxml geopandas
$python_path -m pip install -e .

echo "Python packages for QGIS successfully installed"