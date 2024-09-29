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
filepath_input_edges = homepath + "/data/input/network/processed/edges.gpkg"
filepath_input_edges_studyarea = homepath + "/data/input/network/processed/edges_studyarea.gpkg"
# filepath_input_nodes = homepath + "/data/input/network/processed/nodes.gpkg"
# filepath_input_nodes_studyarea = homepath + "/data/input/network/processed/nodes_studyarea.gpkg"

# import functions
exec(open(homepath + "/src/eval_func.py").read())
exec(open(homepath + "/src/plot_func.py").read())

# load configs (global)
config = yaml.load(open(homepath + "/config/config.yml"), Loader=yaml.FullLoader)
proj_crs = config["proj_crs"]  # projected CRS

# load configs (display)
config_display = yaml.load(open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader)
display_studyarea = config_display["display_study_area"]
display_network = config_display["display_network"]

# set to projected CRS
QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(proj_crs))

# Add basemap
remove_existing_layers(
    [
        "Basemap",
        "Study area",
        "Network edges",
        # "Network nodes"
    ]
)
epsg = proj_crs.replace(":", "")
url = f"type=xyz&url=https://a.tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0&crs={epsg}"
basemap = QgsRasterLayer(url, "Basemap", "wms")
if basemap.isValid():
    QgsProject.instance().addMapLayer(basemap, False)
root = QgsProject.instance().layerTreeRoot()
root.insertLayer(-1, basemap)

# Add study area (if requested)
if display_studyarea == True:

    sa_layer = QgsVectorLayer(filepath_study, "Study area", "ogr")
    if not sa_layer.isValid():
        print("Study area layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(sa_layer)
        draw_simple_polygon_layer(
            "Study area",
            color="250,181,127,128",
            outline_color="black",
            outline_width=0.5,
        )
    zoom_to_layer("Study area")


# Make sure that network extent is not larger than study area
edges = gpd.read_file(filepath_input_edges)
# nodes = gpd.read_file(filepath_input_nodes)
gdf_studyarea = gpd.read_file(filepath_study)

assert (
    edges.crs == gdf_studyarea.crs == proj_crs
), "Edges and study area do not have the same CRS"
# assert (
#     nodes.crs == gdf_studyarea.crs == proj_crs
# ), "Nodes and study area do not have the same CRS"

edges_studyarea = edges.sjoin(gdf_studyarea, predicate="intersects").copy()
edges_studyarea.drop(columns=["index_right"], inplace=True)
# nodes_studyarea = nodes.clip(edges_studyarea.buffer(500).unary_union)

# remove empty geometries
edges_studyarea = edges_studyarea[edges_studyarea.geometry.notna()].reset_index(
    drop=True
)
# nodes_studyarea = nodes_studyarea[nodes_studyarea.geometry.notna()].reset_index(
#     drop=True
# )

# # assert there is one (and only one) Point per node geometry row
# nodes_studyarea = nodes_studyarea.explode(index_parts=False).reset_index(drop=True)
# assert all(
#     nodes_studyarea.geometry.type == "Point"
# ), "Not all node geometries are Points"
# assert all(nodes_studyarea.geometry.is_valid), "Not all node geometries are valid"

# assert there is one (and only one) LineString per edge geometry row
edges_studyarea = edges_studyarea.explode(index_parts=False).reset_index(drop=True)
assert all(
    edges_studyarea.geometry.type == "LineString"
), "Not all edge geometries are LineStrings"
assert all(edges_studyarea.geometry.is_valid), "Not all edge geometries are valid"

# # Makes sure only to include nodes connected to an edge
# nodes_studyarea = nodes_studyarea.loc[
#     nodes_studyarea["node_id"].isin(edges_studyarea["u"])
#     | nodes_studyarea["node_id"].isin(edges_studyarea["v"])
# ]

# save nodes and edges for study area
if not "edge_id" in edges_studyarea.columns:
    edges_studyarea["edge_id"] = edges_studyarea.index
edges_studyarea.to_file(filepath_edges_studyarea, index=False)
# nodes_studyarea.to_file(filepath_nodes_studyarea, index=False)

print("Edges for study area saved!")

if display_network == True:
    edge_layer = QgsVectorLayer(filepath_edges_studyarea, "Network edges", "ogr")
    if not edge_layer.isValid():
        print("Edge layer failed to load!")
    else:
        QgsProject.instance().addMapLayer(edge_layer)
        draw_simple_line_layer(
            "Network edges",
            color="0,0,0,180",
            line_width=0.7,
            line_style="solid",
        )
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

# create subfolders for output and results
os.makedirs(homepath + "/data/output/", exist_ok=True)
os.makedirs(homepath + "/results/", exist_ok=True)

for subfolder in ["plots", "stats", "pdf"]:
    os.makedirs(homepath + f"/results/{subfolder}", exist_ok=True)

layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")

print("script01.py ended successfully.")
