# **** NETWORK EVALUATION *****

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
import shutil

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
edgepath = homepath + "/data/input/network/processed/edges.gpkg"
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
eval_layers_capitalized = [l.title() for l in eval_layers]
remove_existing_layers(eval_layers_capitalized)

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

if any(evaldict.values()):  # if any of the "point", "polygon" dicts is non-empty,

    ### CREATE EVALUATION LAYER IN QGIS

    # define root
    root = QgsProject.instance().layerTreeRoot()

    # make main group for layers
    main_group_name = "2 Evaluation"

    # Remove group if already exists
    remove_existing_group(main_group_name)

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
        # layer_names_capitalized = [l.title() for l in layernames]
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
                output_size_reached=4,
                output_size_not_reached=2,
                output_alpha="255",
            )

            output_layers.append(output_name_within_current)
            output_layers.append(output_name_outside_current)
            res = res | res_current

    point_layers = []
    labels = []

    for k, v in evaldict["point"].items():
        input_fp = v["filepath"]
        point_layer = QgsVectorLayer(input_fp, k, "ogr")
        point_layers.append(point_layer)
        labels.append(k)

    for pl, label in zip(point_layers, labels):
        render_heatmap(pl, label.title())
        output_layers.append(label.title() + " heatmap")

    # print("test")
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

    ### VISUALIZATION (order layers)
    all_layers = input_layers + output_layers

    main_group = root.insertGroup(0, main_group_name)

    # evaldict[geomtype].keys() contains all the group layers (geomtype is one of "point", "polygon")
    for geomtype, geomdict in evaldict.items():
        for sublayer in geomdict.keys():
            layernames = [
                n
                for n in all_layers
                if sublayer in n or sublayer.lower() in n or sublayer.title() in n
            ]
            sub_group = main_group.addGroup(sublayer)
            for n in layernames:
                add_layer_to_group(n, sub_group)

    move_group(main_group_name)

    layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

    if "Basemap" in layer_names:
        move_basemap_back(basemap_name="Basemap")

    # Collapse all groups except the main group just created
    group_names = [group.name() for group in root.children() if group.nodeType() == 0]
    group_names.remove(main_group_name)
    for gn in group_names:
        collapse_layer_group(gn)
    print("Evaluation layer created.")

    # save results of summary statistics
    with open(homepath + "/results/stats/stats_evaluation.json", "w") as opened_file:
        json.dump(res, opened_file, indent=6)

### MESSAGE IN CASE NO EVAL DATA IS PROVIDED
else:
    # remove previous eval data
    evalpath = homepath + "/results/stats/stats_evaluation.json"
    if os.path.exists(evalpath):
        os.remove(evalpath)
    print("No point or polygon files provided, will not run evaluation in script02.")

print("script02.py ended.")
