#!/bin/bash

$1 -m pip install --upgrade shapely
$1 -m pip install --upgrade geopandas --force-reinstall -v geopandas==0.14.0
$1 -m pip install momepy
$1 -m pip install osmnx==1.6.0
$1 -m pip install numpy --force-reinstall -v numpy==1.22.4
$1 -m pip install contextily