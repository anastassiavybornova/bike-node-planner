##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)

# display the study area polygon?
display_studyarea = True  

##### NO CHANGES BELOW THIS LINE

print("01_define_study_area started with user settings:")
print(f"\t * Display user-defined study area: {display_studyarea}")

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
import pandas as pd
import json

# import functions
exec(open(homepath + "/src/eval_func.py").read())

# load configs
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]  # projected CRS
dataforsyning_token = configs["dataforsyning_token"]

# define paths
os.makedirs(homepath + "/data/user_input/", exist_ok=True)
os.makedirs(homepath + "/results/stats/", exist_ok=True)
# define location of municipality boundaries file
filepath_municipalities = (
    homepath + "/data/raw/municipality_boundaries/muni_boundary.gpkg"
)
# define location of study area polygon (union of user-provided municipality polygons)
filepath_study = homepath + "/data/user_input/study_area.gpkg"
stats_path = homepath + "/results/stats/"  # store output jsons here

### READ IN MUNICIPALITIES' DATA
muni = gpd.read_file(filepath_municipalities)

# check list of municipalities for errors
for m in configs["municipalities"]:
    assert m in list(
        muni["kommunekode"]
    ), f"\n Could not find the municipality code {m}. \n Please correct the municipality code in the config.yml file and run this script again!"

# if all kommunekode are correct, filter data set and save a copy
muni = muni[muni.kommunekode.isin(configs["municipalities"])].copy()
muni_merged = gpd.GeoDataFrame({"geometry": [muni.unary_union]}, crs=muni.crs)
muni_merged.to_file(filepath_study, index=False, mode="w")
print(f"\t Study area saved to: {filepath_study}")
print("\t Municipalities included in study area:")
for navn in muni.navn:
    print(f"\t {navn}")

# save summary stats of study area
res = {}  # initialize stats results dictionary
res["area"] = muni_merged.to_crs(proj_crs).unary_union.area
res["municipalities"] = configs["municipalities"]
with open(f"{stats_path}stats_studyarea.json", "w") as opened_file:
    json.dump(res, opened_file, indent=6)

# next, merge municipality data into evaluation layers
print("Merging data layers for study area")
print("Please be patient, this might take a while!")
for evaluation_layer in configs["evaluation_layers"]:
    merge_municipalities(
        configs["municipalities"],
        evaluation_layer,
        input_folder=homepath + "/data/raw/",
        output_folder=homepath + "/data/user_input/",
    )

# set to projected CRS
QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(proj_crs))

if display_studyarea == True:
    # import qgis-based plotting functions
    exec(open(homepath + "/src/plot_func.py").read())

    remove_existing_layers(["Study area", "Basemap", "Ortofoto"])

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


if dataforsyning_token and display_studyarea:
    basemap_name = "topo_skaermkort_daempet"
    url = f"https://api.dataforsyningen.dk/{basemap_name}_DAF?service%3DWMTS%26request%3DGetCapabilities%26token%3D{dataforsyning_token}"
    source = f"crs={proj_crs}&dpiMode=7&format=image/jpeg&layers={basemap_name}&styles=default&tileMatrixSet=View1&tilePixelRatio=0&url={url}"
    basemap = QgsRasterLayer(source, "Basemap", "wms")

    QgsProject.instance().addMapLayer(basemap, False)

    root = QgsProject.instance().layerTreeRoot()

    root.insertLayer(-1, basemap)

    basemap_name = "orto_foraar_wmts"
    url = f"https://api.dataforsyningen.dk/{basemap_name}_DAF?service%3DWMTS%26request%3DGetCapabilities%26token%3D{dataforsyning_token}"
    source = f"crs={proj_crs}&dpiMode=7&format=image/jpeg&layers={basemap_name}&styles=default&tileMatrixSet=KortforsyningTilingDK&tilePixelRatio=0&url={url}"
    ortomap = QgsRasterLayer(source, "Ortofoto", "wms")

    QgsProject.instance().addMapLayer(ortomap, False)

    root.insertLayer(-1, ortomap)

print("01_define_study_area script ended successfully \n")
