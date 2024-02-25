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
exec(open(homepath + "/src/plot_func.py").read())
exec(open(homepath + "/src/eval_func.py").read())

# load configs 
config_display = yaml.load(
    open(homepath + "/config-display.yml"), 
    Loader=yaml.FullLoader
    )

# load communication edges
edges = gpd.read_file(
    homepath + "/data/input/network/communication/edges.gpkg")

# load evaluation data
evaldict = {}

for geomtype in ["point", "linestring", "polygon"]:
    geompath = homepath + f"/data/input/{geomtype}/"
    if os.path.exists(geompath):
        geomlayers = os.listdir(geompath)
        evaldict[geomtype] = {}
        for geomlayer in geomlayers:
            geomlayer_name = geomlayer.replace(".gpkg", "")
            evaldict[geomtype][geomlayer_name] = {}
            evaldict[geomtype][geomlayer_name]["filepath"] = geompath + geomlayer
            evaldict[geomtype][geomlayer_name]["gpkg"] = gpd.read_file(geompath + geomlayer)

# evaluate

# save

# plot

