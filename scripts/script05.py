# import packages
import sys
import os
import warnings

warnings.filterwarnings("ignore")
os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import yaml
import contextily as cx
import re
import glob

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()
if homepath not in sys.path:
    sys.path.append(homepath)  # add project path to PATH

# PATHS
filepath_studyarea = homepath + "/data/input/studyarea/studyarea.gpkg"
filepath_edges = homepath + "/data/input/network/processed/edges_studyarea.gpkg"

# remove preexisting plots (if any)
preexisting_plots = glob.glob(homepath + "/results/plots/*")
for plot in preexisting_plots:
    try:
        os.remove(plot)
    except:
        pass

# read in custom functions
exec(open(homepath + "/src/stat_func.py").read())

# load evaluation data
evaldict = {}

for geomtype in ["point", "linestring", "polygon"]:
    geompath_input = homepath + f"/data/input/{geomtype}/"
    geompath_output = homepath + f"/data/output/{geomtype}/"
    if os.path.exists(geompath_input):

        geomlayers = os.listdir(geompath_input)
        geomlayers = [g for g in geomlayers if not ("gpkg-wal" in g or "gpkg-shm" in g)]
        evaldict[geomtype] = {}
        # read in configs for this geometry type
        config_geomtype = yaml.load(
            open(homepath + f"/config/config-{geomtype}.yml"), Loader=yaml.FullLoader
        )

        for geomlayer in geomlayers:

            geomlayer_name = geomlayer.replace(".gpkg", "")
            evaldict[geomtype][geomlayer_name] = {}

            if geomtype == "point":
                files = os.listdir(geompath_output)
                files = [f for f in files if not ("gpkg-wal" in f or "gpkg-shm" in f)]
                geomlayer_name_out = [f for f in files if geomlayer_name in f][0]
                bufferdistance = int(
                    re.findall("_\d+", geomlayer_name_out)[0].replace("_", "")
                )
                evaldict[geomtype][geomlayer_name]["bufferdistance"] = bufferdistance
                evaldict[geomtype][geomlayer_name]["gpkg_within"] = gpd.read_file(
                    geompath_output + geomlayer_name + f"_within_{bufferdistance}.gpkg"
                )
                evaldict[geomtype][geomlayer_name]["gpkg_outside"] = gpd.read_file(
                    geompath_output + geomlayer_name + f"_outside_{bufferdistance}.gpkg"
                )

            # not implemented yet
            if geomtype == "linestring":
                pass

            if geomtype == "polygon":
                files = os.listdir(geompath_output)
                files = [f for f in files if not ("gpkg-wal" in f or "gpkg-shm" in f)]
                geomlayer_name_out = [f for f in files if geomlayer_name in f][0]
                evaldict[geomtype][geomlayer_name]["bufferdistance"] = int(
                    re.findall("_\d+", geomlayer_name_out)[0].replace("_", "")
                )
                evaldict[geomtype][geomlayer_name]["gpkg"] = gpd.read_file(
                    geompath_output + geomlayer_name_out
                )


# load colors configs (user defined, or if not: automated, or if not: generate now)
config_colors = yaml.load(
    open(homepath + "/config/config-colors-eval.yml"), Loader=yaml.FullLoader
)
if not config_colors:
    config_colors = yaml.load(
        open(homepath + "/config/config-colors-eval-auto.yml"), Loader=yaml.FullLoader
    )
if not config_colors:
    # get colors (as rgb strings) from seaborn colorblind palette
    layernames = sorted([item for v in evaldict.values() for item in v.keys()])
    layercolors = sns.color_palette("colorblind", len(layernames))
    config_colors = {}
    for k, v in zip(layernames, layercolors):
        config_colors[k] = (
            str([int(rgba * 255) for rgba in v]).replace("[", "").replace("]", "")
        )

### READ IN NETWORK DATA
study_area = gpd.read_file(filepath_studyarea)
network_edges = gpd.read_file(filepath_edges)


### READ IN STATS
eval_stats = json.load(open(homepath + "/results/stats/stats_evaluation.json", "r"))

fig, ax = plt.subplots(1, 1)

# plot study area
study_area.plot(ax=ax, color=rgb2hex("250,181,127"), alpha=0.5, zorder=1)
# plot network
network_edges.plot(ax=ax, color="black", linewidth=1)
cx.add_basemap(ax=ax, source=cx.providers.CartoDB.Voyager, crs=study_area.crs)

ax.set_title("Study area & network")

ax.set_axis_off()

fig.savefig(
    homepath + "/results/plots/studyarea_network.png", dpi=300, bbox_inches="tight"
)

# for each polygon layer, plot the amounts of network within
for k, v in evaldict["polygon"].items():

    # k is the name of the layer
    # v is a dict: v["gpkg"] contains the network _within_
    #              v["bufferdistance"] contains the bufferdistance (in meters)
    # plot in color config_colors[k]

    # get stats on percent within
    percent_within = np.round(
        100
        * eval_stats[k]["within"]
        / (eval_stats[k]["outside"] + eval_stats[k]["within"]),
        1,
    )

    # get bufferdistance
    bufferdistance = v["bufferdistance"]

    # plot
    fig, ax = plt.subplots(1, 1)
    network_edges.plot(
        ax=ax,
        color="#D3D3D3",
        linewidth=0.8,
        linestyle="solid",
        zorder=0,
    )
    v["gpkg"].plot(
        ax=ax,
        color=rgb2hex(config_colors[k]),
        linewidth=1.5,
        zorder=1,
        label=f"{percent_within}%",
    )
    ax.set_title(f"{k.capitalize()} within {bufferdistance}m from network")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(homepath + f"/results/plots/{k}.png", dpi=300, bbox_inches="tight")

    plt.close()

# for each point layer, plot points reached / unreached separately (colors!)
for k, v in evaldict["point"].items():

    # k is the layername
    # v is a dict: v["bufferdistance"], v["gpkg_within"], v["gpkg_without"]

    # get stats on percent within / outside

    percent_within = np.round(100 * eval_stats[k]["within"] / eval_stats[k]["total"], 1)

    percent_outside = np.round(100 - percent_within, 1)

    # get bufferdistance
    bufferdistance = v["bufferdistance"]

    fig, ax = plt.subplots(1, 1)
    network_edges.plot(
        ax=ax,
        color="#D3D3D3",
        linewidth=0.8,
        linestyle="solid",
        zorder=0,
    )

    v["gpkg_outside"].plot(
        ax=ax,
        color=rgb2hex(config_colors[k]),
        zorder=1,
        label=f"Outside reach ({percent_outside}%)",
        markersize=2,
        alpha=0.3,
    )

    v["gpkg_within"].plot(
        ax=ax,
        color=rgb2hex(config_colors[k]),
        zorder=2,
        label=f"Within reach ({percent_within}%)",
        markersize=2,
    )
    ax.set_title(f"{k.capitalize()} within {bufferdistance}m from network")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(homepath + f"/results/plots/{k}.png", dpi=300, bbox_inches="tight")

    plt.close()

print("Plots saved to /results/plots/")
print("script05.py ended successfully.")
