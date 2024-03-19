# import packages
import src.graphedit as graphedit
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

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# Load configs
config_display = yaml.load(
    open(homepath + "/config-display.yml"), 
    Loader=yaml.FullLoader
    )
display_network_statistics = config_display["display_network_statistics"]

# INPUT/OUTPUT FILE PATHS
nodes_fp = homepath + "/data/input/network/communication/nodes.gpkg"
edges_fp = homepath + "/data/input/network/communication/edges.gpkg"

edgefile = homepath + "/data/output/network/edges_beta.gpkg"
nodefile = homepath + "/data/output/network/nodes_beta.gpkg"

graph_file = homepath + "/data/output/network/network_graph.graphml"
stats_path = homepath + "/results/stats/stats_network.json"  # store output geopackages here

# load data
nodes = gpd.read_file(nodes_fp)
edges = gpd.read_file(edges_fp)

# process data to be used with osmnx
edges = edges.set_index(["u", "v", "key"])
edges["osmid"] = edges.id
nodes["osmid"] = nodes.id
nodes.set_index("osmid", inplace=True)
nodes["x"] = nodes.geometry.x
nodes["y"] = nodes.geometry.y

G = ox.graph_from_gdfs(nodes, edges)

# check that conversion is successfull
ox_nodes, ox_edges = ox.graph_to_gdfs(G)
assert len(ox_nodes) == len(nodes)
assert len(ox_edges) == len(edges)
del ox_nodes, ox_edges

# convert to undirected
assert nx.is_directed(G) == True
G_undirected = ox.get_undirected(G)
assert nx.is_directed(G_undirected) == False

print("Degrees:", nx.degree_histogram(G_undirected))

print(
    f"The number of connected components is: {nx.number_connected_components(G_undirected)}"
)

# generate an undirected nodes and edges dataframe
nodes_undir, edges_undir = ox.graph_to_gdfs(
    G = G_undirected, 
    nodes = True, 
    edges = True)

# Save component number to edges
comps = [c for c in nx.connected_components(G_undirected)]
comps = sorted(comps, key=len, reverse=True) # sort by length (LCC first)

edges_undir["component"] = None

for edge in G_undirected.edges:
    G_undirected.edges[edge]["nx_edge_id"] = edge

for i, comp in enumerate(comps):
    G_sub = nx.subgraph(
        G_undirected, 
        nbunch=comp
        )
    G_sub_edges = [
        G_sub.edges[e]["nx_edge_id"] for e in G_sub.edges
    ]
    edges_undir.loc[
        G_sub_edges,
        "component"
    ] = i + 1 # (starting to count at 1)

assert len(edges_undir.component.unique()) == len(comps)
assert len(edges_undir.loc[edges_undir.component.isna()]) == 0

# Save degrees to nodes
pd_degrees = pd.DataFrame.from_dict(
    dict(G_undirected.degree), 
    orient="index", 
    columns=["degree"]
)

nodes_undir = nodes_undir.merge(
    pd_degrees, 
    left_index=True, 
    right_index=True
)

# Export
if os.path.exists(edgefile):
    os.remove(edgefile)
if os.path.exists(nodefile):
    os.remove(nodefile)

ox.save_graphml(G_undirected, graph_file)
edges_undir.to_file(edgefile, mode="w")
nodes_undir.to_file(nodefile, mode="w")

# save component edges separately
comppath = homepath + "/data/output/network/components/"

os.makedirs(
    comppath, 
    exist_ok=True
    )

zfill_regex = "{:0" + str(len(str(len(comps)))) + "d}" # add leading 0s to filename if needed
for c in edges_undir.component.unique():
    edges_undir.loc[edges_undir["component"]==c].to_file(
        comppath + "comp" + zfill_regex.format(c) + ".gpkg",
        index = False
        )

### Summary statistics of network
res = {}  # initialize stats results dictionary
res["node_count"] = len(G_undirected.nodes)
res["edge_count"] = len(G_undirected.edges)
res["node_degrees"] = dict(nx.degree(G_undirected))
with open(stats_path, "w") as opened_file:
    json.dump(res, opened_file, indent=6)
print(f"Network statistics saved to {stats_path}")

# ### Visualization
# remove_existing_layers(["Edges (beta)", "Nodes (beta)", "Input edges", "Input nodes"])

if display_network_statistics:

    remove_existing_layers(["Component"])

    comp_files = os.listdir(comppath)
    comp_numbers = [int(re.findall(r'\d+', file)[0]) for file in comp_files]
    comp_layer_names = []
    
    # create random colors (one for every comp) from seaborn colorblind palette
    layercolors = sns.color_palette("colorblind", len(comp_files))
    comp_colors = {}
    for k, v in zip(comp_numbers, layercolors):
        comp_colors[k] = str([int(rgba*255) for rgba in v]).replace("[", "").replace("]", "")

    for comp_file, comp_number in zip(comp_files, comp_numbers):

        comp_layer_name = f"Component {str(comp_number)}"
        
        comp_layer = QgsVectorLayer(
            comppath + comp_file,
            comp_layer_name,
            "ogr"
            )    
        
        QgsProject.instance().addMapLayer(comp_layer)
        
        draw_simple_line_layer(
            comp_layer_name, 
            color=comp_colors[comp_number], 
            line_width=0.5, 
            line_style="dash"
        )

        comp_layer_names.append(comp_layer_name)
    
    group_layers(
        group_name = "Connected components",
        layer_names = comp_layer_names,
        remove_group_if_exists=True,
    )


    # group_layers(
    #     "Connected components",
    #     comp_layer_names,
    #     remove_group_if_exists=True,
    # )
#     input_edges = QgsVectorLayer(edges_fp, "Input edges", "ogr")
#     input_nodes = QgsVectorLayer(nodes_fp, "Input nodes", "ogr")

#     QgsProject.instance().addMapLayer(input_edges)
#     QgsProject.instance().addMapLayer(input_nodes)

#     draw_simple_point_layer("Input nodes", marker_size=2, color="black")

#     zoom_to_layer("Input edges")


# if display_network_layer:
#     vlayer_edges = QgsVectorLayer(edgefile, "Edges (beta)", "ogr")
#     if not vlayer_edges.isValid():
#         print("Layer failed to load!")
#     else:
#         QgsProject.instance().addMapLayer(vlayer_edges)

#     vlayer_nodes = QgsVectorLayer(nodefile, "Nodes (beta)", "ogr")
#     if not vlayer_nodes.isValid():
#         print("Layer failed to load!")
#     else:
#         QgsProject.instance().addMapLayer(vlayer_nodes)
#         draw_simple_point_layer("Nodes (beta)", marker_size=2)

#     draw_categorical_layer("Edges (beta)", "component", line_width=1)
#     draw_categorical_layer("Nodes (beta)", "degree", marker_size=3)

#     zoom_to_layer("Edges (beta)")

# if display_input_data == False and display_network_layer == True:
#     group_layers(
#         "Make Beta Network",
#         ["Edges (beta)", "Nodes (beta)"],
#         remove_group_if_exists=True,
#     )

# if display_input_data == True and display_network_layer == False:
#     group_layers(
#         "Make Beta Network",
#         ["Input edges", "Input nodes"],
#         remove_group_if_exists=True,
#     )

# if display_input_data == True and display_network_layer == True:
#     group_layers(
#         "Make Beta Network",
#         ["Input edges", "Input nodes", "Edges (beta)", "Nodes (beta)"],
#         remove_group_if_exists=True,
#     )

# layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

# if "Study area" in layer_names:
#     # Change symbol for study layer
#     draw_simple_polygon_layer(
#         "Study area",
#         color="250,181,127,0",
#         outline_color="red",
#         outline_width=0.7,
#     )

#     move_study_area_front()

# if "Basemap" in layer_names:
#     move_basemap_back(basemap_name="Basemap")
# if "Ortofoto" in layer_names:
#     move_basemap_back(basemap_name="Ortofoto")

print("script05.py finished")