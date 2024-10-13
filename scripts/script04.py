import os
import shutil
import yaml
import pickle
import json
import random

random.seed(42)
import warnings

warnings.filterwarnings("ignore")
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
from src.plot_func import *

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# Load configs
config_display = yaml.load(
    open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader
)
display_network_statistics = config_display["display_network_statistics"]

# INPUT/OUTPUT FILE PATHS

for fp in [
    homepath + "/data/output/network/",
    homepath + "/data/output/network/components/",
    homepath + "/data/results/",
    homepath + "/data/results/stats/",
]:
    os.makedirs(fp, exist_ok=True)

# input
# filepath_nodes_input = homepath + "/data/input/network/processed/nodes_studyarea.gpkg"
filepath_edges_input = homepath + "/data/input/network/processed/edges.gpkg"

# output
filepath_edge_output = homepath + "/data/output/network/edges.gpkg"
filepath_node_output = homepath + "/data/output/network/nodes.gpkg"

graph_file = homepath + "/data/output/network/network_graph.pickle"
stats_path = homepath + "/results/stats/stats_network.json"  # store output here

# load data
# nodes = gpd.read_file(filepath_nodes_input)
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
print(f"Degree histogram: {degree_histogram}")
print(f"Number of nodes without edges: {degree_histogram[0]}.")
print(f"Removing {degree_histogram[0]} nodes from the network.")
nodes_to_remove = [node for node in G.nodes if nx.degree(G, node) == 0]
G.remove_nodes_from(nodes_to_remove)
degree_histogram = nx.degree_histogram(G)
print(f"Degree histogram (updated): {degree_histogram}")

# using momepy to get nodes and edges gdf with corresponding labels and geometry objects
nodes, edges = momepy.nx_to_gdf(net=G, points=True, lines=True)

### Add degree labels to nodes
degrees = pd.DataFrame.from_dict(dict(G.degree), orient="index", columns=["degree"])
nodes = nodes.merge(degrees, left_index=True, right_index=True)

### Connected components (& add component labels to edges gdf)
print(f"The number of connected components is: {nx.number_connected_components(G)}")
comps = [c for c in nx.connected_components(G)]
comps = sorted(comps, key=len, reverse=True)  # sort by length (LCC first)
i = 1  # component count (starting to count at 1)
for comp in comps:

    # for each component, make subgraph
    G_sub = nx.subgraph(G, nbunch=comp)

    # if subgraph has at least 1 edge:
    assert len(G_sub.edges) > 0, "Component has no edges"

    G_sub_edges = [G_sub.edges[e]["edge_id"] for e in G_sub.edges]
    edges.loc[edges.edge_id.isin(G_sub_edges), "component"] = int(i)
    i += 1

# Export edges, nodes, and graph
if os.path.exists(filepath_edge_output):
    os.remove(filepath_edge_output)
if os.path.exists(filepath_node_output):
    os.remove(filepath_node_output)

edges.to_file(filepath_edge_output, mode="w")
nodes.to_file(filepath_node_output, mode="w")

with open(graph_file, "wb") as f:
    pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
# # to read back in:
# with open(graph_file, 'rb') as f:
#     G = pickle.load(f)

### save comp edges as SEPARATE files (for plotting)
comppath = homepath + "/data/output/network/components/"
# first remove pre-existing files if any
if os.path.exists(comppath):
    shutil.rmtree(fp)
    os.makedirs(comppath, exist_ok=True)

comps_index = []
for comp, group in edges.groupby("component"):
    comps_index.append(int(comp))
    group.copy().reset_index(drop=True).to_file(comppath + f"{int(comp)}.gpkg")

### Summary statistics of network
res = {}  # initialize stats results dictionary
res["node_count"] = len(G.nodes)
res["edge_count"] = len(G.edges)
res["components"] = len(comps)
# res["node_degrees"] = dict(nx.degree(G))

with open(stats_path, "w") as opened_file:
    json.dump(res, opened_file, indent=6)
print(f"Network statistics saved to {stats_path}")

### Visualization
remove_existing_layers(["Edges (beta)", "Nodes (beta)", "Input edges", "Input nodes"])

if display_network_statistics:

    remove_existing_layers(["Component"])

    comp_layer_names = []

    # create random colors (one for every comp) from seaborn colorblind palette
    layercolors = sns.color_palette("colorblind", len(comps_index))
    comp_colors = {}
    comp_colors_hex = {}
    for k, v in zip(comps_index, layercolors):
        comp_colors[k] = (
            str([int(rgba * 255) for rgba in v]).replace("[", "").replace("]", "")
        )
        comp_colors_hex[k] = v

    for comp in comps_index:

        comp_layer_name = f"Component {str(comp)}"
        comp_layer = QgsVectorLayer(comppath + f"{comp}.gpkg", comp_layer_name, "ogr")

        QgsProject.instance().addMapLayer(comp_layer)

        draw_simple_line_layer(
            comp_layer_name,
            color=comp_colors[comp],
            line_width=1,
            line_style="dash",
        )

        comp_layer_names.append(comp_layer_name)

    group_name = "4 Connected components"
    group_layers(
        group_name=group_name,
        layer_names=comp_layer_names,
        remove_group_if_exists=True,
    )


layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

turn_off_layer_names = [
    "Network edges",
    # "Network nodes"
]

turn_off_layer_names = [t for t in turn_off_layer_names if t in layer_names]

turn_off_layers(turn_off_layer_names)

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")

move_group(group_name)

# make matplotlib plots of each component

for comp in comps_index:
    gdf = gpd.read_file(comppath + f"{comp}.gpkg")
    fig, ax = plt.subplots(1, 1)
    gdf.plot(ax=ax, color=comp_colors_hex[comp])
    ax.set_axis_off()
    ax.set_title(f"Component nr {comp}")
    cx.add_basemap(ax=ax, source=cx.providers.CartoDB.Voyager, crs=gdf.crs)
    fig.savefig(
        homepath + f"/results/plots/component{comp}.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

print(f"Component plots saved to {homepath}/results/plots/")
print("script04.py ended successfully.")
