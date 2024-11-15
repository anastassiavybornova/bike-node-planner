# ***** LOOP LENGHTS *****

import os
import shutil
import yaml
import pickle
import json
import random

random.seed(42)
import warnings

warnings.filterwarnings("ignore")
import shapely
import geopandas as gpd
import networkx as nx
import pandas as pd
import networkx as nx
import seaborn as sns
import contextily as cx
import momepy
import matplotlib.pyplot as plt
from qgis.core import *
from qgis.utils import *

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# Load configs
config = yaml.load(
    open(homepath + "/config/config-topological-analysis.yml"), Loader=yaml.FullLoader
)
[loop_length_min, loop_length_max] = config["loop_length_range"]

# display?
config_display = yaml.load(
    open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader
)
display_loop_lengths = config_display["display_loop_lengths"]

# load custom functions
exec(open(homepath + "/src/plot_func.py").read())
exec(open(homepath + "/src/eval_func.py").read())

# INPUT/OUTPUT FILE PATHS

for fp in [
    homepath + "/data/output/network/",
    homepath + "/data/output/network/topology/",
    homepath + "/data/results/",
]:
    os.makedirs(fp, exist_ok=True)

# input
filepath_edges_input = homepath + "/data/input/network/processed/edges.gpkg"

# output
topo_folder = homepath + "/data/output/network/topology/"

# load data
edges_in = gpd.read_file(filepath_edges_input)

# convert to networkx object with momepy
G = momepy.gdf_to_nx(
    gdf_network=edges_in,
    multigraph=False,
    #    integer_labels=True, # only in momepy 0.8+
    directed=False,
)

# remove degree 0 nodes
degree_histogram = nx.degree_histogram(G)
nodes_to_remove = [node for node in G.nodes if nx.degree(G, node) == 0]
G.remove_nodes_from(nodes_to_remove)
degree_histogram = nx.degree_histogram(G)

# using momepy to get nodes and edges gdf with corresponding labels and geometry objects
nodes, edges = momepy.nx_to_gdf(net=G, points=True, lines=True)

# ### Visualization
remove_existing_layers(["too short loops", "ideal range loops", "too long loops"])

### Classify loop lengths

# as in https://martinfleischmann.net/fixing-missing-geometries-in-a-polygonized-network/
linestrings = (
    edges.geometry.copy()
)  # our geopandas.GeoSeries of linestrings representing street network
collection = shapely.GeometryCollection(linestrings.array)  # combine to a single object
noded = shapely.node(collection)  # add missing nodes
polygonized = shapely.polygonize(
    noded.geoms
)  # polygonize based on an array of nodded parts
polygons = gpd.GeoSeries(polygonized.geoms)  # create a GeoSeries from parts

# create geodataframe of loops, where we will save evaluation column
loops = gpd.GeoDataFrame(geometry=polygons, crs=edges.crs)
loops["length_km"] = loops.length / 1000

loops["length_class"] = loops.length_km.apply(
    lambda x: classify_looplength(
        length_km=x, loop_length_min=loop_length_min, loop_length_max=loop_length_max
    )
)

loops.to_file(topo_folder + f"loops_length_classification.gpkg", index=False)

for classification in loops.length_class.unique():
    fp = topo_folder + f"loops_{classification}.gpkg"
    loops[loops["length_class"] == classification].to_file(fp, index=False)

if display_loop_lengths:
    layer_names = []
    for classification in loops.length_class.unique():
        layer_name = classification.replace("_", " ") + " loops"
        layer_names.append(layer_name)
        fp = topo_folder + f"loops_{classification}.gpkg"
        layer = QgsVectorLayer(fp, layer_name, "ogr")
        QgsProject.instance().addMapLayer(layer)
        draw_simple_polygon_layer(
            layer_name,
            color=loop_classification_colors[classification],
            outline_color="0,0,0,0",
            outline_width=0,
        )

    group_name = "6 Loop lengths"
    group_layers(
        group_name=group_name,
        layer_names=layer_names,
        remove_group_if_exists=True,
    )
    move_group(group_name)

print("script06.py ended successfully.")