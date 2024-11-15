# ****** EDGE LENGTH CLASSIFICATION ******

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
[ideal_length_lower, ideal_length_upper] = config["ideal_length_range"]
max_length = config["max_length"]

# display?
config_display = yaml.load(
    open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader
)
display_edge_lengths = config_display["display_edge_lengths"]

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
remove_existing_layers(
    [
        "too short edges",
        "ideal range edges",
        "above ideal edges",
        "too long edges",
    ]
)

### Classify edge lengths (in km)

edges["length_km"] = edges.length / 1000
edges["length_class"] = edges.length_km.apply(
    lambda x: classify_edgelength(
        length_km=x,
        ideal_length_lower=ideal_length_lower,
        ideal_length_upper=ideal_length_upper,
        max_length=max_length,
    )
)

edges.to_file(topo_folder + f"edges_length_classification.gpkg", index=False)

for classification in edges.length_class.unique():
    fp = topo_folder + f"edges_{classification}.gpkg"
    edges[edges["length_class"] == classification].to_file(fp, index=False)

if display_edge_lengths:
    layer_names = []
    for classification in edges.length_class.unique():
        layer_name = classification.replace("_", " ") + " edges"
        layer_names.append(layer_name)
        fp = topo_folder + f"edges_{classification}.gpkg"
        layer = QgsVectorLayer(fp, layer_name, "ogr")
        QgsProject.instance().addMapLayer(layer)
        draw_simple_line_layer(
            layer_name,
            color=edge_classification_colors[classification],
            line_width=1,
            line_style="solid",  # TODO
        )

    group_name = "5 Edge lengths"
    group_layers(
        group_name=group_name,
        layer_names=layer_names,
        remove_group_if_exists=True,
    )
    move_group(group_name)

print("script05.py ended successfully.")
