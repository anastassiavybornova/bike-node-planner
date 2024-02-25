##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)

# display technical layer of edges (output of this step)?
display_technicallayer = True  

# display the entire input data set (for all of DK)? 
display_inputdata = False  

##### NO CHANGES BELOW THIS LINE

print("02_make_technical_network script started with user settings:")
print(f"\t * Display input data: {display_inputdata}")
print(f"\t * Display technical layer: {display_technicallayer}")

### SETUP

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# add project path to PATH
import sys

if homepath not in sys.path:
    sys.path.append(homepath)

# import python packages
import os

os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import yaml
from qgis.core import *

# import qgis-based plotting functions
exec(open(homepath + "/src/plot_func.py").read())

# load configs
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]  # projected CRS

print("done: setup")

### PATHS

# make folders for results (if they don't exist yet)
os.makedirs(homepath + "/data/processed/workflow_steps", exist_ok=True)

# define paths to input files
node_inpath = homepath + "/data/raw/network/nodes.gpkg"
edge_inpath = homepath + "/data/raw/network/edges.gpkg"

# define paths to output files
nodetech_outpath = homepath + "/data/processed/workflow_steps/nodes_technical.gpkg"
edgetech_outpath = homepath + "/data/processed/workflow_steps/edges_technical.gpkg"

# define location of study area polygon (user-provided)
filepath_study = homepath + "/data/user_input/study_area.gpkg"

print("done: paths")

### STUDY AREA

# read in study area polygon provided by the user
study_area = gpd.read_file(filepath_study)
study_area = study_area.to_crs(proj_crs)

# Remove layers from project if they exist already
remove_existing_layers(["beta data (pre-network)"])

print("done: study area")

### READ IN INPUT DATA (BETA NETWORK FROM FOLKERSMA)

nodes = gpd.read_file(node_inpath)
nodes = nodes.to_crs(proj_crs)

edges = gpd.read_file(edge_inpath)
edges = edges.to_crs(proj_crs)

print("done: input data")

### LIMIT INPUT DATA TO STUDY AREA EXTENT

assert nodes.crs == study_area.crs
assert edges.crs == study_area.crs

# only keep those nodes and edges that are within the study area
nodes = nodes[nodes.intersects(study_area.loc[0, "geometry"])].copy()
nodes.reset_index(drop=True, inplace=True)

edges = edges[edges.intersects(study_area.loc[0, "geometry"])].copy()
edges.reset_index(drop=True, inplace=True)

print("done: limit to study area")

### PROCESS NODE & EDGE DATA

# remove empty geometries
edges = edges[edges.geometry.notna()].reset_index(drop=True)
nodes = nodes[nodes.geometry.notna()].reset_index(drop=True)

# assert there is one (and only one) LineString per edge geometry row
nodes = nodes.explode(index_parts=False).reset_index(drop=True)
assert all(nodes.geometry.type == "Point")
assert all(nodes.geometry.is_valid)

# assert there is one (and only one) Point per node geometry row
edges = edges.explode(index_parts=False).reset_index(drop=True)
assert all(edges.geometry.type == "LineString")
assert all(edges.geometry.is_valid)

# project to projected crs
nodes.to_crs(proj_crs, inplace=True)
edges.to_crs(proj_crs, inplace=True)

print("done: process data")

### SAVE TECHNICAL NODE AND EDGE DATA TO FILE
# these are the "technical data" layers that will be used by all consecutive scripts FOR PLOTTING
if os.path.exists(nodetech_outpath):
    os.remove(nodetech_outpath)
if os.path.exists(edgetech_outpath):
    os.remove(edgetech_outpath)
nodes.to_file(nodetech_outpath, mode="w")
edges.to_file(edgetech_outpath, mode="w")
print(f"Technical data layer for nodes in study area saved to: {nodetech_outpath}")
print(f"Technical data layer for edges in study area saved to: {edgetech_outpath}")


### IF REQUESTED BY USER, DISPLAY LAYERS

remove_existing_layers(["Input data", "Technical network"])

QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(proj_crs))

# input data (entire raw data set from folkersma)
if display_inputdata == True:
    input_layer = QgsVectorLayer(edge_inpath, "Input data", "ogr")
    if not input_layer.isValid():
        print("Layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(input_layer)
        draw_recent_simple_line_layer(color="green", width=0.7, line_style="dash")


# output data (folkersma data cut to study area and cleaned)
if display_technicallayer == True:
    tech_layer = QgsVectorLayer(edgetech_outpath, "Technical network", "ogr")
    if not tech_layer.isValid():
        print("Layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(tech_layer)
        draw_recent_simple_line_layer(color="blue", width=0.7, line_style="solid")


if display_inputdata and display_technicallayer:
    group_layers(
        group_name="Make technical network layer",
        layer_names=["Input data", "Technical network"],
    )

    zoom_to_layer("Technical network")

if display_inputdata == True and display_technicallayer == False:
    group_layers(
        group_name="Make technical network layer",
        layer_names=["Input data"],
    )

    zoom_to_layer("Input data")

if display_inputdata == False and display_technicallayer == True:
    group_layers(
        group_name="Make technical network layer", layer_names=["Technical network"]
    )

    zoom_to_layer("Technical network")


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

print("02_make_technical_network script ended successfully \n")
