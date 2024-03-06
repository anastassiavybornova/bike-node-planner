# import packages
import sys
import os
os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import json
import yaml
import contextily as cx
import re

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()
if homepath not in sys.path:
    sys.path.append(homepath) # add project path to PATH

# read in custom functions
exec(open(homepath + "/src/stat_func.py").read())

# load evaluation data
evaldict = {}

for geomtype in ["point", "linestring", "polygon"]:
    geompath_input = homepath + f"/data/input/{geomtype}/"
    geompath_output = homepath + f"/data/output/{geomtype}/"
    if os.path.exists(geompath_input):

        geomlayers = os.listdir(geompath_input)
        geomlayers = [g for g in geomlayers if not("gpkg-wal" in g or "gpkg-shm" in g)]
        evaldict[geomtype] = {}
        # read in configs for this geometry type
        config_geomtype = yaml.load(
            open(homepath + f"/config-{geomtype}.yml"), 
            Loader=yaml.FullLoader
            )
        
        for geomlayer in geomlayers:
            
            geomlayer_name = geomlayer.replace(".gpkg", "")
            evaldict[geomtype][geomlayer_name] = {}
    
            if geomtype == "point":
                files = os.listdir(geompath_output)
                files = [f for f in files if not("gpkg-wal" in f or "gpkg-shm" in f)]
                geomlayer_name_out = [f for f in files if geomlayer_name in f][0]
                bufferdistance = int(re.findall("_\d+", geomlayer_name_out)[0].replace("_", ""))
                evaldict[geomtype][geomlayer_name]["bufferdistance"] = bufferdistance
                evaldict[geomtype][geomlayer_name]["gpkg_within"] = gpd.read_file(
                    geompath_output + geomlayer_name + f"_within_{bufferdistance}.gpkg")
                evaldict[geomtype][geomlayer_name]["gpkg_outside"] = gpd.read_file(
                    geompath_output + geomlayer_name + f"_outside_{bufferdistance}.gpkg")
            
            # not implemented yet
            if geomtype == "linestring":
                pass

            if geomtype == "polygon":
                files = os.listdir(geompath_output)
                files = [f for f in files if not("gpkg-wal" in f or "gpkg-shm" in f)]
                geomlayer_name_out = [f for f in files if geomlayer_name in f][0]
                evaldict[geomtype][geomlayer_name]["bufferdistance"] = int(re.findall("_\d+", geomlayer_name_out)[0].replace("_", ""))
                evaldict[geomtype][geomlayer_name]["gpkg"] = gpd.read_file(
                    geompath_output + geomlayer_name_out)


# load colors configs (user defined, or if not: automated, or if not: generate now)
config_colors = yaml.load(
    open(homepath + "/config-colors-eval.yml"), 
    Loader=yaml.FullLoader)
if not config_colors:
    config_colors = yaml.load(
        open(homepath + "/config-colors-eval-auto.yml"), 
        Loader=yaml.FullLoader)
if not config_colors:
    # get colors (as rgb strings) from seaborn colorblind palette 
    layernames = sorted([item for v in evaldict.values() for item in v.keys()])
    layercolors = sns.color_palette("colorblind", len(layernames))
    config_colors = {}
    for k, v in zip(layernames, layercolors):
        config_colors[k] = str([int(rgba*255) for rgba in v]).replace("[", "").replace("]", "")

# ### READ IN NETWORK DATA

# muni = gpd.read_file(homepath + "/data/raw/municipality_boundaries/muni_boundary.gpkg")

# # paths
# path = homepath + "/data/processed/workflow_steps/"
# edge_file = "network_edges_no_parallel.gpkg"
# # node_file = "nodes_edges_parallel.gpkg"

# # read in
# edges = gpd.read_file(path + edge_file)
# # nodes = gpd.read_file(path + node_file)

# ### READ IN EVALUATION RESULTS

# # paths
# filenames = os.listdir(homepath + "/results/data/")
# path = homepath + "/results/data/"

# # read in segments
# # segments = gpd.read_file(path + "segments_slope.gpkg")

# # define distance thresholds for polygon layers
# dist_veri = configs["polygon_buffers"]["dist_verify"]
# dist_agri = configs["polygon_buffers"]["dist_agriculture"]
# dist_culture = configs["polygon_buffers"]["dist_culture"]
# dist_nature = configs["polygon_buffers"]["dist_nature"]
# dist_summer = configs["polygon_buffers"]["dist_summer"]

# # define distance thresholds for point layers
# dist_faci = configs["point_distances"]["dist_facilities"]
# dist_serv = configs["point_distances"]["dist_service"]
# dist_pois = configs["point_distances"]["dist_pois"]

# # read in polygon layers
# agri_path = path + f"agriculture_network_{dist_agri}.gpkg"
# if os.path.exists(agri_path):
#     agriculture = gpd.read_file(agri_path)
# else:
#     agriculture = gpd.GeoDataFrame()

# verify_path = path + f"verify_network_{dist_veri}.gpkg"
# if os.path.exists(verify_path):
#     verify = gpd.read_file(verify_path)
# else:
#     verify = gpd.GeoDataFrame()

# culture_path = path + f"culture_network_{dist_culture}.gpkg"
# if os.path.exists(culture_path):
#     culture = gpd.read_file(culture_path)
# else:
#     culture = gpd.GeoDataFrame()

# nature_path = path + f"nature_network_{dist_nature}.gpkg"
# if os.path.exists(nature_path):
#     nature = gpd.read_file(nature_path)
# else:
#     nature = gpd.GeoDataFrame()

# summer_path = path + f"summer_network_{dist_summer}.gpkg"
# if os.path.exists(summer_path):
#     summer = gpd.read_file(summer_path)
# else:
#     summer = gpd.GeoDataFrame()

# ## FOR NOW: MERGE POINT LAYERS
# # (later: make output 1 layer)

# facilities_within = gpd.read_file(path + f"facilities_within_reach_{dist_faci}.gpkg")
# facilities_outside = gpd.read_file(path + f"facilities_outside_reach_{dist_faci}.gpkg")
# facilities = pd.concat([facilities_outside, facilities_within], ignore_index=True)

# service_within = gpd.read_file(path + f"service_within_reach_{dist_serv}.gpkg")
# service_outside = gpd.read_file(path + f"service_outside_reach_{dist_serv}.gpkg")
# service = pd.concat([service_outside, service_within], ignore_index=True)

# pois_within = gpd.read_file(path + f"pois_within_reach_{dist_pois}.gpkg")
# pois_outside = gpd.read_file(path + f"pois_outside_reach_{dist_pois}.gpkg")
# pois = pd.concat([pois_outside, pois_within], ignore_index=True)

# ### READ IN STATS RESULTS
# # with open(homepath + "/results/stats/stats_studyarea.json") as opened_file:
# #     stats_studyarea = json.load(opened_file)
# #
# # with open(homepath + "/results/stats/stats_evaluation.json") as opened_file:
# #     stats_evaluation = json.load(opened_file)
# #
# # with open(homepath + "/results/stats/stats_network.json") as opened_file:
# #     stats_network = json.load(opened_file)

# ### MAKE FIGURE
# stats_fig = plot_overview(
#     my_markersize=30,
#     my_linewidth=3,
#     configs=configs,
#     colors=colors,
#     edges=edges,
#     muni=muni,
#     nature=nature,
#     agriculture=agriculture,
#     culture=culture,
#     verify=verify,
#     summer=summer,
#     facilities=facilities,
#     service=service,
#     pois=pois
#     )

# stats_fig.savefig(homepath + f"/results/plots/evaluation.png", dpi = 300)
# print(f"Summary statistics plot saved")

# print("script06.py finished")