import os
import glob
import sys
import yaml
import json
import geopandas as gpd
import seaborn as sns
from ast import literal_eval
from qgis.core import *
import warnings

warnings.filterwarnings("ignore")

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
    open(homepath + "/config/config-display.yml"), Loader=yaml.FullLoader
)

# load edges
edgepath = homepath + "/data/input/network/processed/edges_studyarea.gpkg"
edges = gpd.read_file(edgepath)

# load evaluation data
evaldict = {}

geomtypes = [
    "point",
    # linestring, # tbi
    "polygon",
]

for geomtype in geomtypes:
    geompath = homepath + f"/data/input/{geomtype}/"
    if os.path.exists(geompath):
        geomlayers = os.listdir(geompath)
        geomlayers = [g for g in geomlayers if not ("gpkg-wal" in g or "gpkg-shm" in g)]
        evaldict[geomtype] = {}
        # read in configs for this geometry type
        config_geomtype = yaml.load(
            open(homepath + f"/config/config-{geomtype}.yml"), Loader=yaml.FullLoader
        )
        for geomlayer in geomlayers:
            geomlayer_name = geomlayer.replace(".gpkg", "")
            evaldict[geomtype][geomlayer_name] = {}
            evaldict[geomtype][geomlayer_name]["filepath"] = geompath + geomlayer
            evaldict[geomtype][geomlayer_name]["gpkg"] = gpd.read_file(
                geompath + geomlayer
            )
            evaldict[geomtype][geomlayer_name]["bufferdistance"] = config_geomtype[
                geomlayer_name
            ]
            # make filepath for results
            os.makedirs(geompath.replace("input", "output"), exist_ok=True)

# remove existing layers...
eval_layers = [item for v in evaldict.values() for item in v]
remove_existing_layers(eval_layers)

# remove existing OUTPUT files, if any
for geomtype in geomtypes:
    geompath = homepath + f"/data/output/{geomtype}/"
    if os.path.exists(geompath):
        preexisting_files = glob.glob(geompath + "*")
    for f in preexisting_files:
        try:
            os.remove(f)
        except:
            pass

# define root
root = QgsProject.instance().layerTreeRoot()

# make main group for layers
main_group_name = "Evaluation"

# Check if group already exists
for group in [child for child in root.children() if child.nodeType() == 0]:
    if group.name() == main_group_name:
        root.removeChildNode(group)

# Initialize list of layers for layer grouping
input_layers = []
output_layers = []

# load colors for plotting of evaluation layers, if available; if not, create own palette
config_colors = yaml.load(
    open(homepath + "/config/config-colors-eval.yml"), Loader=yaml.FullLoader
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
    # and save as separate yml
    with open(homepath + "/config/config-colors-eval-auto.yml", "w") as opened_file:
        yaml.dump(config_colors, opened_file, indent=6)

# initialize stats results dictionary
res = {}

# evaluate point layers
if evaldict["point"]:
    for k, v in evaldict["point"].items():
        # create darker value for reached items
        rgb_shaded = rgb_shade(config_colors[k])
        mydist = v["bufferdistance"]
        (
            output_name_within_current,
            output_name_outside_current,
            res_current,
        ) = evaluate_export_plot_point(
            input_fp=v["filepath"],
            within_reach_output_fp=v["filepath"]
            .replace("input", "output")
            .replace(".gpkg", f"_within_{mydist}.gpkg"),
            outside_reach_output_fp=v["filepath"]
            .replace("input", "output")
            .replace(".gpkg", f"_outside_{mydist}.gpkg"),
            network_edges=edges,
            dist=mydist,
            name=k,
            output_color_reached=config_colors[k],
            output_color_not_reached=rgb_shaded,
            display_output=config_display["display_evaluation_output"],
            output_size_reached=3,
            output_size_not_reached=3,
            output_alpha="255",
        )

        output_layers.append(output_name_within_current)
        output_layers.append(output_name_outside_current)
        res = res | res_current

# evaluate linestring layers
# TODO
# if evaldict["linestring"]:
#     # not implemented
#     pass

# evaluate polygon layers
if evaldict["polygon"]:
    for k, v in evaldict["polygon"].items():
        mydist = v["bufferdistance"]
        (input_name_current, output_name_current, res_current) = (
            evaluate_export_plot_poly(
                input_fp=v["filepath"],
                output_fp=v["filepath"]
                .replace("input", "output")
                .replace(".gpkg", f"_{mydist}.gpkg"),
                network_edges=edges,
                dist=mydist,
                name=k,
                type_col="types",
                fill_color_rgb=config_colors[k],
                outline_color_rgb=config_colors[k],
                line_color_rgb=config_colors[k],
                line_width=1,
                line_style="solid",
                plot_categorical=False,
                fill_alpha="100",
                outline_alpha="200",
                display_input=config_display["display_evaluation_input"],
                display_output=config_display["display_evaluation_output"],
            )
        )
        input_layers.append(input_name_current)
        output_layers.append(output_name_current)
        res = res | res_current

# save results of summary statistics
with open(homepath + "/results/stats/stats_evaluation.json", "w") as opened_file:
    json.dump(res, opened_file, indent=6)

### VISUALIZATION (order layers)
all_layers = input_layers + output_layers

main_group = root.insertGroup(0, main_group_name)

# evaldict[geomtype].keys() contains all the group layers (geomtype is one of "point", "polygon")
for geomtype, geomdict in evaldict.items():
    for sublayer in geomdict.keys():
        layernames = [n for n in all_layers if sublayer in n or sublayer.lower() in n]
        sub_group = main_group.addGroup(sublayer)
        for n in layernames:
            add_layer_to_group(n, sub_group)

layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

if "Basemap" in layer_names:
    move_basemap_back(basemap_name="Basemap")

print("script02.py ended successfully.")
