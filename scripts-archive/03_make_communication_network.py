##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)

# display communication layer (output of this step)?
display_communicationlayer = True

# display entire input data set (for all of DK)?
display_inputdata = False


##### NO CHANGES BELOW THIS LINE

print("03_make_communication_network script started with user settings:")
print(f"\t * Display input data: {display_inputdata}")
print(f"\t * Display communication layer: {display_communicationlayer}")
print("Please be patient, this might take a while!")

### SETUP

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# add project path to PATH
import sys

if homepath not in sys.path:
    sys.path.append(homepath)

# import python packages
from qgis.core import *
import geopandas as gpd
from shapely.geometry import LineString
import os
import yaml
import json
from src import graphedit

# import qgis-based plotting functions
exec(open(homepath + "/src/plot_func.py").read())

# load configs
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]  # projected CRS
municipality_codes = configs["municipalities"]

### PATHS

# output data
output_file_edges = (
    homepath + "/data/processed/workflow_steps/network_edges_with_parallel.gpkg"
)
output_file_nodes = (
    homepath + "/data/processed/workflow_steps/nodes_edges_parallel.gpkg"
)

output_file_edges_no_parallel = (
    homepath + "/data/processed/workflow_steps/network_edges_no_parallel.gpkg"
)
results_path = homepath + "/results/data/"  # store output geopackages here

print("setup done!")

# input data
nodepath = homepath + "/data/raw/network/nodes.gpkg"
edgepath = homepath + "/data/raw/network/edges.gpkg"

### STUDY AREA

# define location of study area polygon (user-provided)
filepath_study = homepath + "/data/user_input/study_area.gpkg"

# read in study area polygon provided by the user
study_area = gpd.read_file(filepath_study)
study_area = study_area.to_crs(proj_crs)

### LOAD INPUT DATA AND PROJECT

nodes = gpd.read_file(nodepath)
edges = gpd.read_file(edgepath)

print("data read in!")

### LIMIT INPUT DATA TO STUDY AREA EXTENT

nodes.to_crs(proj_crs, inplace=True)
edges.to_crs(proj_crs, inplace=True)

assert nodes.crs == study_area.crs
assert edges.crs == study_area.crs

# only keep those nodes and edges that are within the study area
nodes = nodes[nodes.intersects(study_area.loc[0, "geometry"])].copy()
nodes.reset_index(drop=True, inplace=True)

edges = edges[edges.intersects(study_area.loc[0, "geometry"])].copy()
edges.reset_index(drop=True, inplace=True)

### PROCESS INPUT DATA TO FIND AND REMOVE PARALLEL EDGES

# create distinct column names for unique id
edges["edge_id"] = edges.index
assert len(edges) == len(edges.edge_id.unique())
nodes["node_id"] = nodes.id
assert len(nodes) == len(nodes.node_id.unique())

# assign edges initial start and end nodes
edges = graphedit.assign_edges_start_end_nodes(edges, nodes)

# find all child nodes with parents that are not dead ends
child_nodes = nodes[(nodes.refmain.notna()) & (nodes.deadend == 0)]

edges["modified"] = False

# assign edges from child nodes with parents to parent nodes
for ix, row in child_nodes.iterrows():
    idx = ix
    # ID of this child node
    this_node_id = row.node_id

    # geometry of the child nodes parent node
    parent_geom = nodes.loc[
        nodes.node_id == int(child_nodes.loc[ix, "refmain"])
    ].geometry.values[0]
    # print(f"idx {idx}, step 1")

    if parent_geom.distance(row.geometry) > 100:
        continue
    else:
        # all edges which have this child node as their start node
        edges_start = edges.loc[edges.u == this_node_id]

        # all edges which have this child node as their end node
        edges_end = edges.loc[edges.v == this_node_id]
        # print(f"idx {idx}, step 2")

        for ix, row in edges_start.iterrows():
            # get coordinate in edge linestring
            edge_coords = list(row.geometry.coords)

            # replace start coordinate (child node) with geometry of parent node
            edge_coords[0] = parent_geom.coords[0]

            # create new linestring from updated coordinates
            new_linestring = LineString(edge_coords)

            # update edge geometry
            edges.loc[ix, "geometry"] = new_linestring

            # mark edge as modified
            edges.loc[ix, "modified"] = True
            # print(f"idx {idx}, step 3")

        for ix, row in edges_end.iterrows():
            # get coordinate in edge linestring
            edge_coords = list(row.geometry.coords)

            # replace end coordinate (child node) with geometry of parent node
            edge_coords[-1] = parent_geom.coords[0]

            # create new linestring from updated coordinates
            new_linestring = LineString(edge_coords)

            # update edge geometry
            edges.loc[ix, "geometry"] = new_linestring

            # mark edge as modified
            edges.loc[ix, "modified"] = True
            # print(f"idx {idx}, step 4")

# drop old u,v columns
edges.drop(["u", "v"], axis=1, inplace=True)

# find new start and end nodes
edges = graphedit.assign_edges_start_end_nodes(edges, nodes)

# find edges with same start and end node (but could still be on different roads!)
edges["key"] = 0

# Set u to be to be the smaller one of u,v nodes (based on node id) - to identify parallel edges between u,v / v,u matches
graphedit.order_edge_nodes(edges)

edges = graphedit.find_parallel_edges(edges)

# delete modified edges whith same u and v
edges.drop(
    edges.loc[(edges.u == edges.v) & (edges.modified == True)].index, inplace=True
)

# find parallel edges of approximate same length
edges["drop"] = False
edges["length"] = edges.geometry.length

grouped = edges.groupby(["u", "v"])

for name, group in grouped:
    if len(group) > 1:
        # compare length of all members in groups pair wise
        group_lengths = group.length.to_list()

        duplicates = []
        # mark as duplicate if length difference is less than 20 %
        for i in range(len(group_lengths)):
            for j in range(i + 1, len(group_lengths)):
                if (
                    abs(
                        (
                            (group_lengths[i] - group_lengths[j])
                            / ((group_lengths[i] + group_lengths[j]) / 2)
                        )
                        * 100
                    )
                    < 8
                ):
                    duplicates.append((group_lengths[i], group_lengths[j]))

        length_of_edges_to_drop = set([min(d) for d in duplicates])

        edges.loc[
            group.loc[group.length.isin(length_of_edges_to_drop)].index, "drop"
        ] = True

# nodes used by new network edges
nodes_in_use = nodes.loc[nodes.node_id.isin(set(edges.u.to_list() + edges.v.to_list()))]

# edges without parallel edges
edges_no_parallel = edges.loc[edges["drop"] == False]

# assert len(nodes.loc[nodes.ismain == True]) == len(
#     nodes_in_use.loc[nodes_in_use.ismain == True]
# )

### SAVE COMMUNICATION NODE AND EDGE DATA TO FILE
# these are the "communication data" layers that will be used by all consecutive scripts FOR PLOTTING

assert len(edges) == len(edges.edge_id.unique())
assert len(edges_no_parallel) == len(edges_no_parallel.edge_id.unique())
assert len(nodes_in_use) == len(nodes_in_use.id.unique())

if os.path.exists(output_file_nodes):
    os.remove(output_file_nodes)

if os.path.exists(output_file_edges):
    os.remove(output_file_edges)

if os.path.exists(output_file_edges_no_parallel):
    os.remove(output_file_edges_no_parallel)

nodes_in_use.to_file(output_file_nodes, mode="w")
edges.to_file(output_file_edges, mode="w")

edges_no_parallel.to_file(output_file_edges_no_parallel, mode="w")

# # save summary stats of communication network
# res = {} # initialize stats results dictionary
# res["total_length"] = edges_no_parallel.to_crs(proj_crs).length.sum()
# res["edges_count"] = len(edges_no_parallel)
# res["nodes_in_use"] = len(nodes_in_use)
# with open(f"{stats_path}stats_communication_network.json", "w") as opened_file:
#     json.dump(res, opened_file, indent = 6)

### REMOVE LAYERS IF THEY EXIST ALREADY
remove_existing_layers(
    [
        "input edges",
        "input nodes",
        "output edges",
        "output nodes",
        "communication layer",
    ]
)

### IF REQUESTED BY USER, DISPLAY LAYERS

if display_inputdata:
    input_edges = QgsVectorLayer(edgepath, "input edges", "ogr")
    QgsProject.instance().addMapLayer(input_edges)
    draw_recent_simple_line_layer(color="purple", width=0.5)

    input_nodes = QgsVectorLayer(nodepath, "input nodes", "ogr")
    QgsProject.instance().addMapLayer(input_nodes)

    draw_categorical_layer(
        "input nodes",
        "ismain",
        outline_width=0.0,
        alpha=200,
        marker_size=2,
    )

    zoom_to_layer("input edges")

if display_communicationlayer:
    parallel_edges = QgsVectorLayer(output_file_edges, "output edges", "ogr")
    QgsProject.instance().addMapLayer(parallel_edges)

    draw_categorical_layer("output edges", "drop", alpha=180, line_style="solid")

    no_parallel_edges = QgsVectorLayer(
        output_file_edges_no_parallel, "communication layer", "ogr"
    )
    QgsProject.instance().addMapLayer(no_parallel_edges)

    draw_recent_simple_line_layer(color="red", width=1)

    output_nodes = QgsVectorLayer(output_file_nodes, "output nodes", "ogr")
    QgsProject.instance().addMapLayer(output_nodes)

    draw_categorical_layer(
        "output nodes",
        "ismain",
        outline_width=0.0,
        alpha=200,
        marker_size=3,
    )

    zoom_to_layer("output edges")

if display_inputdata and display_communicationlayer:
    group_layers(
        "Make communication layer",
        [
            "input edges",
            "input nodes",
            "output edges",
            "communication layer",
            "output nodes",
        ],
        remove_group_if_exists=True,
    )

if display_communicationlayer and not display_inputdata:
    group_layers(
        "Make communication layer",
        ["output edges", "communication layer", "output nodes"],
        remove_group_if_exists=True,
    )

if display_inputdata and not display_communicationlayer:
    group_layers(
        "Make communication layer",
        [
            "input edges",
            "input nodes",
        ],
        remove_group_if_exists=True,
    )

print("layers added")

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

print("03_make_communication_network script ended successfully \n")
