##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)

display_input_data = False
display_network_layer = True

### NO CHANGES BELOW THIS LINE

print("06_compute_network_statistics script started with user settings:")
print(f"\t Display input data: {display_input_data}")
print(f"\t Display network layer: {display_network_layer}")

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()
exec(open(homepath + "/src/plot_func.py").read())

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

# load configs
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]

# INPUT/OUTPUT FILE PATHS
nodes_fp = homepath + "/data/processed/workflow_steps/nodes_edges_parallel.gpkg"
edges_fp = homepath + "/data/processed/workflow_steps/network_edges_no_parallel.gpkg"
edgefile = homepath + "/data/processed/workflow_steps/edges_beta.gpkg"
nodefile = homepath + "/data/processed/workflow_steps/nodes_beta.gpkg"
graph_file = homepath + "/data/processed/workflow_steps/network_graph.json"
stats_path = homepath + "/results/stats/"  # store output geopackages here

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

G_undirected = ox.get_undirected(G)

assert nx.is_directed(G) == True
assert nx.is_directed(G_undirected) == False

print("Degrees:", nx.degree_histogram(G_undirected))

print(
    f"The number of connected components is: {nx.number_connected_components(G_undirected)}"
)
# Save component number to edges
comps = [c for c in nx.connected_components(G_undirected)]

edges["component"] = None

for i, comp in enumerate(comps):
    index_list = list(G_undirected.edges(comp))

    for index in index_list:
        try:
            edges.loc[index, "component"] = i + 1  # start counting at 1
        except KeyError:
            edges.loc[(index[1], index[0]), "component"] = i + 1  # start counting at 1

# rename component nr 1 (the biggest one) into "LCC"
edges.loc[edges["component"] == 1, "component"] = "LCC"

assert len(edges.component.unique()) == len(comps)
assert len(edges.loc[edges.component.isna()]) == 0

# Save degrees to nodes
pd_degrees = pd.DataFrame.from_dict(
    dict(G_undirected.degree), orient="index", columns=["degree"]
)
nodes = nodes.merge(pd_degrees, left_index=True, right_index=True)

# Export
if os.path.exists(edgefile):
    os.remove(edgefile)
if os.path.exists(nodefile):
    os.remove(nodefile)

ox.save_graphml(G_undirected, graph_file)
edges.to_file(edgefile, mode="w")
nodes.to_file(nodefile, mode="w")

### Summary statistics of network
res = {}  # initialize stats results dictionary
res["node_count"] = len(G_undirected.nodes)
res["edge_count"] = len(G_undirected.edges)
res["node_degrees"] = dict(nx.degree(G))
with open(f"{stats_path}stats_network.json", "w") as opened_file:
    json.dump(res, opened_file, indent=6)
print(f"Network statistics saved to {stats_path}stats_network.json")

### Visualization
remove_existing_layers(["Edges (beta)", "Nodes (beta)", "Input edges", "Input nodes"])

# display in QGIS
if display_input_data:
    input_edges = QgsVectorLayer(edges_fp, "Input edges", "ogr")
    input_nodes = QgsVectorLayer(nodes_fp, "Input nodes", "ogr")

    QgsProject.instance().addMapLayer(input_edges)
    QgsProject.instance().addMapLayer(input_nodes)

    draw_simple_line_layer(
        "Input edges", color="grey", line_width=0.5, line_style="dash"
    )
    draw_simple_point_layer("Input nodes", marker_size=2, color="black")

    zoom_to_layer("Input edges")


if display_network_layer:
    vlayer_edges = QgsVectorLayer(edgefile, "Edges (beta)", "ogr")
    if not vlayer_edges.isValid():
        print("Layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(vlayer_edges)

    vlayer_nodes = QgsVectorLayer(nodefile, "Nodes (beta)", "ogr")
    if not vlayer_nodes.isValid():
        print("Layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(vlayer_nodes)
        draw_simple_point_layer("Nodes (beta)", marker_size=2)

    draw_categorical_layer("Edges (beta)", "component", line_width=1)
    draw_categorical_layer("Nodes (beta)", "degree", marker_size=3)

    zoom_to_layer("Edges (beta)")

if display_input_data == False and display_network_layer == True:
    group_layers(
        "Make Beta Network",
        ["Edges (beta)", "Nodes (beta)"],
        remove_group_if_exists=True,
    )

if display_input_data == True and display_network_layer == False:
    group_layers(
        "Make Beta Network",
        ["Input edges", "Input nodes"],
        remove_group_if_exists=True,
    )

if display_input_data == True and display_network_layer == True:
    group_layers(
        "Make Beta Network",
        ["Input edges", "Input nodes", "Edges (beta)", "Nodes (beta)"],
        remove_group_if_exists=True,
    )

layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

if "Study area" in layer_names:
    # Change symbol for study layer
    draw_simple_polygon_layer(
        "Study area",
        color="250,181,127,0",
        outline_color="red",
        outline_width=0.7,
    )

    move_study_area_front()

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")
if "Ortofoto" in layer_names:
    move_basemap_back(basemap_name="Ortofoto")

print("06_compute_network_statistics script ended successfully \n")