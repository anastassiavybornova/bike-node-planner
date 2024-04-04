import os
import sys
import yaml
import geopandas as gpd
from qgis.core import *

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()
# add project path to PATH
if homepath not in sys.path:
    sys.path.append(homepath)

# load custom functions
exec(open(homepath + "/src/tech-to-comm.py").read())
exec(open(homepath + "/src/eval_func.py").read())
exec(open(homepath + "/src/plot_func.py").read())

config_display = yaml.load(
    open(homepath + "/config-display.yml"), 
    Loader=yaml.FullLoader
    )

communication_edges_exist = os.path.isfile(
    homepath + "/data/input/network/communication/edges.gpkg")
technical_edges_exist = os.path.isfile(
    homepath + "/data/input/network/technical/edges.gpkg")
technical_nodes_exist = os.path.isfile(
    homepath + "/data/input/network/technical/nodes.gpkg")

if communication_edges_exist:
    print("Communication network found. Will ignore data (if any) in /data/input/network/technical/")
elif not (technical_edges_exist and technical_nodes_exist): 
    print("No network data found. Please provide network data in /data/input/communication/ and/or /data/input/technical/")
else:
    print("Technical network found. Creating a communication network...")
    # read in technical network data
    nodes_studyarea = gpd.read_file(
        homepath + "/data/input/network/technical/nodes.gpkg")
    edges_studyarea = gpd.read_file(
        homepath + "/data/input/network/technical/edges.gpkg")
    # tech-to-comm workflow
    nodes_communication, edges_communication, edges_communication_parallel = technical_to_communication(
        node_gdf = nodes_studyarea,
        edge_gdf = edges_studyarea 
        )
    # save to files
    communication_folder = homepath + "/data/input/network/communication/"
    os.makedirs(communication_folder, exist_ok=True)
    nodes_communication.to_file(
        communication_folder + "nodes.gpkg", 
        index = False)
    edges_communication.to_file(
        communication_folder + "edges.gpkg", 
        index = False)
    edges_communication_parallel.to_file(
        communication_folder + "edges_parallel.gpkg", 
        index = False)
    print("...Communication nodes and edges for study area saved!")

# check again whether communication edges exist
communication_edges_path = homepath + "/data/input/network/communication/edges.gpkg"
communication_edges_exist = os.path.isfile(communication_edges_path)
# if so, plot edges
if communication_edges_exist:
    remove_existing_layers(["Network"])
    vlayer_network = QgsVectorLayer(communication_edges_path, "Network", "ogr")
    QgsProject.instance().addMapLayer(vlayer_network)
    draw_simple_line_layer("Network", color="black", line_width=0.5, line_style="dash")
    zoom_to_layer("Network")

print("script02.py finished")