# ***** STUDY AREA AND NETWORK VISUALIZATION *****

# import python packages
import sys
import os

os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import yaml
import geopandas as gpd
from qgis.core import *
import warnings

warnings.filterwarnings("ignore")

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# add project path to PATH
if homepath not in sys.path:
    sys.path.append(homepath)

# FILEPATHS
filepath_study = homepath + "/data/input/studyarea/studyarea.gpkg"
filepath_edges = homepath + "/data/input/network/processed/edges.gpkg"
# raw nodes & edges - only for plotting
fp_nodes_raw = homepath + "/data/input/network/raw/nodes.gpkg"
fp_edges_raw = homepath + "/data/input/network/raw/edges.gpkg"

# import functions
exec(open(homepath + "/src/eval_func.py").read())
exec(open(homepath + "/src/plot_func.py").read())

# load configs (global)
config = yaml.load(open(homepath + "/config/config.yml"), Loader=yaml.FullLoader)
proj_crs = config["proj_crs"]  # projected CRS

# load configs (display)
config_display = yaml.load(
    open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader
)
display_studyarea = config_display["display_study_area"]
display_network = config_display["display_network"]
display_technical = config_display["display_technical"]

# set to projected CRS
QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(proj_crs))

# Remove existing layers
remove_existing_layers(
    [
        "Basemap",
        "Study area",
        "Network edges",
        "Network nodes",
        "Network edges (raw data)",
        "Network nodes (raw data)",
    ]
)

# Remove existing group
group_name = "1 Raw data"
remove_existing_group(group_name)

# Add basemap
epsg = proj_crs.replace(":", "")
url = f"type=xyz&url=https://a.tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0&crs={epsg}"
basemap = QgsRasterLayer(url, "Basemap", "wms")
if basemap.isValid():
    QgsProject.instance().addMapLayer(basemap, False)
root = QgsProject.instance().layerTreeRoot()
root.insertLayer(-1, basemap)

# Make sure that crs matches
edges = gpd.read_file(filepath_edges)
gdf_studyarea = gpd.read_file(filepath_study)
assert (
    edges.crs == gdf_studyarea.crs == proj_crs
), "Edges and study area do not have the same CRS"

if display_network and os.path.exists(filepath_edges):
    edge_layer = QgsVectorLayer(filepath_edges, "Network edges", "ogr")
    if not edge_layer.isValid():
        print("Edge layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(edge_layer, False)
        add_layer_to_position(edge_layer, -1)
        draw_simple_line_layer(
            "Network edges",
            color="0,0,0,180",
            line_width=0.7,
            line_style="solid",
        )

        # move_layer("Network edges", position=-2)

    # node_layer = QgsVectorLayer(filepath_nodes_studyarea, "Network nodes", "ogr")
    # if not node_layer.isValid():
    #     print("Node layer failed to load!")
    # else:
    #     QgsProject.instance().addMapLayer(node_layer)
    #     draw_simple_point_layer(
    #         "Network nodes",
    #         color="0,0,0,255",
    #         outline_color="black",
    #         outline_width=0.5,
    #         marker_size=3,
    #     )

# Add study area (if requested)
if display_studyarea and os.path.exists(filepath_study):

    sa_layer = QgsVectorLayer(filepath_study, "Study area", "ogr")
    if not sa_layer.isValid():
        print("Study area layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(sa_layer, False)
        add_layer_to_position(sa_layer, -1)
        draw_simple_polygon_layer(
            "Study area",
            color="250,181,127,128",
            outline_color="black",
            outline_width=0.5,
        )
        zoom_to_layer("Study area")

if display_technical and os.path.exists(fp_edges_raw) and os.path.exists(fp_nodes_raw):

    # read in raw nodes and edges to check CRS for plotting
    edges_raw = gpd.read_file(fp_edges_raw)
    assert (
        edges_raw.crs == gdf_studyarea.crs == proj_crs
    ), "Raw edges and study area do not have the same CRS"
    nodes_raw = gpd.read_file(fp_nodes_raw)
    assert (
        nodes_raw.crs == gdf_studyarea.crs == proj_crs
    ), "Raw nodes and study area do not have the same CRS"

    # raw edges
    edges_raw_layer = QgsVectorLayer(fp_edges_raw, "Network edges (raw data)", "ogr")
    if not edges_raw_layer.isValid():
        print("Edge layer (raw data) failed to load!")
    else:
        QgsProject.instance().addMapLayer(edges_raw_layer)
        draw_simple_line_layer(
            "Network edges (raw data)",
            color="169, 169, 169,255",
            line_width=1,
            line_style="dash",
        )

    # raw nodes
    nodes_raw_layer = QgsVectorLayer(fp_nodes_raw, "Network nodes (raw data)", "ogr")
    if not nodes_raw_layer.isValid():
        print("Node layer (raw data) failed to load!")
    else:
        QgsProject.instance().addMapLayer(nodes_raw_layer)
        draw_simple_point_layer(
            "Network nodes (raw data)",
            color="169, 169, 169,255",
            outline_color="0, 0, 0,255",
            outline_width=0.2,
            marker_size=2,
        )

    root = QgsProject.instance().layerTreeRoot()

    # Add to layer group
    # Turn off layer group by default
    group_name = "1 Raw data"
    group_layers(
        group_name=group_name,
        layer_names=[
            "Network edges (raw data)",
            "Network nodes (raw data)",
        ],
        remove_group_if_exists=True,
    )

    QgsProject.instance().layerTreeRoot().findGroup(
        group_name
    ).setItemVisibilityChecked(False)

    move_group(group_name, position=-1)


# create subfolders for output and results
os.makedirs(homepath + "/data/output/", exist_ok=True)
os.makedirs(homepath + "/results/", exist_ok=True)

for subfolder in ["plots", "stats", "pdf"]:
    os.makedirs(homepath + f"/results/{subfolder}", exist_ok=True)

# Collapse all groups
group_names = [group.name() for group in root.children() if group.nodeType() == 0]
for gn in group_names:
    collapse_layer_group(gn)

layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")

print("script01.py ended successfully.")
