# import packages

import geopandas as gpd
import osmnx as ox
import networkx as nx
import pandas as pd
import os
import yaml
import networkx as nx
from qgis.core import *
import json
import re
import seaborn as sns
import random

random.seed(42)
import warnings

warnings.filterwarnings("ignore")
import glob

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# Load configs
config_display = yaml.load(
    open(homepath + "/config-display.yml"), Loader=yaml.FullLoader
)
display_network_statistics = config_display["display_network_statistics"]

# INPUT/OUTPUT FILE PATHS
# input
filepath_nodes_input = homepath + "/data/input/network/processed/nodes_studyarea.gpkg"
filepath_edges_input = homepath + "/data/input/network/processed/edges_studyarea.gpkg"

# output
filepath_edge_output = homepath + "/data/output/network/edges.gpkg"
filepath_node_output = homepath + "/data/output/network/nodes.gpkg"

graph_file = homepath + "/data/output/network/network_graph.graphml"
stats_path = (
    homepath + "/results/stats/stats_network.json"
)  # store output geopackages here

# load data
nodes = gpd.read_file(filepath_nodes_input)
edges = gpd.read_file(filepath_edges_input)

# Drop edges with missing start and end nodes
edges.dropna(subset=["u", "v"], inplace=True)
edges["key"].fillna(0, inplace=True)

# process data to be used with osmnx
edges = edges.set_index(["u", "v", "key"])
edges["osmid"] = edges.edge_id
nodes["osmid"] = nodes.node_id
nodes.set_index("osmid", inplace=True)
nodes["x"] = nodes.geometry.x
nodes["y"] = nodes.geometry.y

G = ox.graph_from_gdfs(nodes, edges)

# check that conversion is successfull
ox_nodes, ox_edges = ox.graph_to_gdfs(G)
assert len(ox_nodes) == len(
    nodes
), "Number of graph nodes not equal to number of input nodes"
assert len(ox_edges) == len(
    edges
), "Number of graph edges not equal to number of input edges"
del ox_nodes, ox_edges

# convert to undirected
assert nx.is_directed(G) == True, "Graph is not directed"
G_undirected = ox.get_undirected(G)
assert nx.is_directed(G_undirected) == False, "Graph is directed"

print("Degrees:", nx.degree_histogram(G_undirected))

print(
    f"The number of connected components is: {nx.number_connected_components(G_undirected)}"
)

# generate an undirected nodes and edges dataframe
nodes_undir, edges_undir = ox.graph_to_gdfs(G=G_undirected, nodes=True, edges=True)

# Save component number to edges
comps = [c for c in nx.connected_components(G_undirected)]
comps = sorted(comps, key=len, reverse=True)  # sort by length (LCC first)

edges_undir["component"] = None

for edge in G_undirected.edges:
    G_undirected.edges[edge]["nx_edge_id"] = edge

for i, comp in enumerate(comps):
    G_sub = nx.subgraph(G_undirected, nbunch=comp)
    G_sub_edges = [G_sub.edges[e]["nx_edge_id"] for e in G_sub.edges]
    edges_undir.loc[G_sub_edges, "component"] = i + 1  # (starting to count at 1)

assert len(edges_undir.component.unique()) == len(
    comps
), "Unexpected number of components"
assert (
    len(edges_undir.loc[edges_undir.component.isna()]) == 0
), "Some edges have no component"

# Save degrees to nodes
pd_degrees = pd.DataFrame.from_dict(
    dict(G_undirected.degree), orient="index", columns=["degree"]
)

nodes_undir = nodes_undir.merge(pd_degrees, left_index=True, right_index=True)

# Export
if os.path.exists(filepath_edge_output):
    os.remove(filepath_edge_output)
if os.path.exists(filepath_node_output):
    os.remove(filepath_node_output)

ox.save_graphml(G_undirected, graph_file)
edges_undir.to_file(filepath_edge_output, mode="w")
nodes_undir.to_file(filepath_node_output, mode="w")

### save component edges separately

# make directory
os.makedirs(homepath + "/data/output/network/", exist_ok=True)
comppath = homepath + "/data/output/network/components/"
os.makedirs(comppath, exist_ok=True)

# remove preexisting files, if any
preexisting_files = glob.glob(comppath + "*")
for file in preexisting_files:
    try:
        os.remove(file)
    except:
        pass

zfill_regex = (
    "{:0" + str(len(str(len(comps)))) + "d}"
)  # add leading 0s to filename if needed
for c in edges_undir.component.unique():
    compfile = comppath + "comp" + zfill_regex.format(c) + ".gpkg"
    edges_undir.loc[edges_undir["component"] == c].to_file(compfile, index=False)

### Summary statistics of network
res = {}  # initialize stats results dictionary
res["node_count"] = len(G_undirected.nodes)
res["edge_count"] = len(G_undirected.edges)
res["components"] = len(comps)
res["node_degrees"] = dict(nx.degree(G_undirected))

with open(stats_path, "w") as opened_file:
    json.dump(res, opened_file, indent=6)
print(f"Network statistics saved to {stats_path}")

# ### Visualization
# remove_existing_layers(["Edges (beta)", "Nodes (beta)", "Input edges", "Input nodes"])

if display_network_statistics:

    remove_existing_layers(["Component"])

    comp_files = os.listdir(comppath)
    comp_numbers = [int(re.findall(r"\d+", file)[0]) for file in comp_files]
    comp_layer_names = []

    # create random colors (one for every comp) from seaborn colorblind palette
    layercolors = sns.color_palette("colorblind", len(comp_files))
    comp_colors = {}
    for k, v in zip(comp_numbers, layercolors):
        comp_colors[k] = (
            str([int(rgba * 255) for rgba in v]).replace("[", "").replace("]", "")
        )

    for comp_file, comp_number in zip(comp_files, comp_numbers):

        comp_layer_name = f"Component {str(comp_number)}"

        comp_layer = QgsVectorLayer(comppath + comp_file, comp_layer_name, "ogr")

        QgsProject.instance().addMapLayer(comp_layer)

        draw_simple_line_layer(
            comp_layer_name,
            color=comp_colors[comp_number],
            line_width=1,
            line_style="dash",
        )

        comp_layer_names.append(comp_layer_name)

    group_layers(
        group_name="Connected components",
        layer_names=comp_layer_names,
        remove_group_if_exists=True,
    )


layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

turn_off_layer_names = ["Network edges", "Network nodes"]

turn_off_layer_names = [t for t in turn_off_layer_names if t in layer_names]

turn_off_layers(turn_off_layer_names)

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")

print("script04.py ended successfully.")
