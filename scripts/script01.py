# import python packages
import sys
import os
os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import yaml
from qgis.core import *

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# add project path to PATH
if homepath not in sys.path:
    sys.path.append(homepath)

# import functions
exec(open(homepath + "/src/eval_func.py").read())

# load configs (global)
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
config = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = config["proj_crs"]  # projected CRS

# load configs (display)
configdisplayfile = os.path.join(homepath, "config-display.yml")  # filepath of config-display file
config_display = yaml.load(open(configdisplayfile), Loader=yaml.FullLoader)
display_studyarea = config_display["display_study_area"]

# set to projected CRS
QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(proj_crs))

# define location of study area polygon (union of user-provided municipality polygons)
filepath_study = homepath + "/data/input/studyarea/studyarea.gpkg"

if display_studyarea == True:
    # import qgis-based plotting functions
    exec(open(homepath + "/src/plot_func.py").read())

    remove_existing_layers(["Study area", "Basemap"])

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