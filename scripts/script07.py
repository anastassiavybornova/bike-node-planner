# ***** SUMMARIZE RESULTS AND MAKE PLOTS *****

# import packages
import sys
import os
import warnings

warnings.filterwarnings("ignore")
os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import yaml
import contextily as cx
import re
import glob
import seaborn as sns
import random
random.seed(42)

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()
if homepath not in sys.path:
    sys.path.append(homepath)  # add project path to PATH

# load custom functions
exec(open(homepath + "/src/plot_func.py").read())
exec(open(homepath + "/src/utils.py").read())

# PATHS
filepath_studyarea = homepath + "/data/input/studyarea/studyarea.gpkg"
filepath_edges = homepath + "/data/input/network/processed/edges.gpkg"

# remove preexisting plots (if any)
preexisting_plots = glob.glob(homepath + "/results/plots/*")
for plot in preexisting_plots:
    try:
        os.remove(plot)
    except:
        pass

# load evaldict
evaldict = load_evaluation_data(homepath)

if any(evaldict.values()):
    # load colors configs (user defined, or if not: automated, or if not: generate now)
    config_colors = yaml.load(
        open(homepath + "/config/config-colors-eval.yml"), Loader=yaml.FullLoader
    )
    if not config_colors:
        config_colors = yaml.load(
            open(homepath + "/config/config-colors-eval-auto.yml"), Loader=yaml.FullLoader
        )
    if not config_colors:
        # get colors (as rgb strings) from seaborn colorblind palette
        layernames = sorted([item for v in evaldict.values() for item in v.keys()])
        layercolors = sns.color_palette("colorblind", len(layernames))
        config_colors = {}
        for k, v in zip(layernames, layercolors):
            config_colors[k] = (
                str([int(rgba * 255) for rgba in v]).replace("[", "").replace("]", "")
            )

### READ IN NETWORK DATA
study_area = gpd.read_file(filepath_studyarea)
network_edges = gpd.read_file(filepath_edges)

### READ IN STATS
eval_path = homepath + "/results/stats/stats_evaluation.json"
if os.path.exists(eval_path):
    eval_stats = json.load(open(eval_path, "r"))

### STUDY AREA (OUTPUT OF SCRIPT01)
try:
    plot_study_area(study_area, network_edges, homepath)
    print("Plotted study area")
except:
    print("Failed to plot study area, passing")

### POINT AND POLYGON LAYERS (OUTPUT OF SCRIPT02)
# for each polygon layer, plot the amounts of network within
if evaldict["polygon"]:
    for layerkey, layervalue in evaldict["polygon"].items():
        try:
            plot_polygon_layer(eval_stats, layerkey, layervalue, network_edges, config_colors, homepath)
            print(f"Plotted {layerkey} polygon layer")
        except:
            print(f"Failed to plot {layerkey} polygon layer, passing")

# for each point layer, plot points reached / unreached separately (colors!)
if evaldict["point"]:
    for layerkey, layervalue in evaldict["point"].items():
        try:
            plot_point_layer(eval_stats, layerkey, layervalue, network_edges, config_colors, homepath)
            print(f"Plotted {layerkey} point layer")
        except:
            print(f"Failed to plot {layerkey} point layer, passing")

### SLOPES (OUTPUT OF SCRIPT03)
if os.path.exists(homepath + "/data/output/elevation/edges_slope.gpkg"):
    try:
        plot_slopes(homepath)
        print("Plotted slopes")
    except:
        print("Failed to plot slopes, passing")

### COMPONENTS (OUTPUT OF SCRIPT04)
try:
    plot_components(homepath=homepath)
    print("Plotted disconnected components")
except:
    print("Failed to plot disconnected components, passing")

### EDGE LENGTHS (OUTPUT OF SCRIPT05)
try:
    plot_edge_lengths(
        homepath=homepath, edge_classification_colors=edge_classification_colors
    )
    print("Plotted edge lengths")
except:
    print("Failed to plot edge lengths, passing")

### LOOP LENGTHS (OUTPUT OF SCRIPT06)
try:
    plot_loop_lengths(
        homepath=homepath, loop_classification_colors=loop_classification_colors
    )
    print("Plotted loop lengths")
except:
    print("Failed to plot loop lengths, passing")

print("Plots saved to /results/plots/")
print("script07.py ended successfully.")