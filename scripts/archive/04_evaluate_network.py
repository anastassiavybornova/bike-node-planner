##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)

display_input = True
display_output = True

##### NO CHANGES BELOW THIS LINE

### SETUP

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# add project path to PATH
import sys

if homepath not in sys.path:
    sys.path.append(homepath)

# import python packages
import os
import os.path

os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import pandas as pd
from shapely import strtree
import json

# load configs and colors
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]  # projected CRS
colorfile = os.path.join(
    homepath, "colors.yml"
)  # load color dictionary for visualization
colors = yaml.load(open(colorfile), Loader=yaml.FullLoader)

# import functions
exec(open(homepath + "/src/plot_func.py").read())
exec(open(homepath + "/src/eval_func.py").read())

### PATHS
study_path = homepath + "/data/processed/workflow_steps/network_edges_no_parallel.gpkg"
eval_path = homepath + "/data/user_input/"  # where is evaluation data
results_path = homepath + "/results/data/"  # store output geopackages here
stats_path = homepath + "/results/stats/"  # store output json here
for path in [eval_path, results_path, stats_path]:
    os.makedirs(path, exist_ok=True)

# define distance thresholds for polygon layers
dist_veri = configs["polygon_buffers"]["dist_verify"]
dist_agri = configs["polygon_buffers"]["dist_agriculture"]
dist_culture = configs["polygon_buffers"]["dist_culture"]
dist_nature = configs["polygon_buffers"]["dist_nature"]
dist_summer = configs["polygon_buffers"]["dist_summer"]

# define distance thresholds for point layers
dist_faci = configs["point_distances"]["dist_facilities"]
dist_serv = configs["point_distances"]["dist_service"]
dist_pois = configs["point_distances"]["dist_pois"]

print("04_evaluate_network script started with user settings:")
print(f"\t * Display input: {display_input}; display_output: {display_output}")
print(f"\t * Distance thresholds for polygon layers:")
print(f"\t \t - Areas to verify: {dist_veri}m")
print(f"\t \t - Agricultural areas: {dist_agri}m")
print(f"\t \t - Culture areas: {dist_culture}m")
print(f"\t \t - Nature areas: {dist_nature}m")
print(f"\t \t - Summerhouse areas: {dist_summer}m")
print(f"\t * Distance thresholds for point layers:")
print(f"\t \t - Facilities: {dist_faci}m")
print(f"\t \t - Service: {dist_serv}m")
print(f"\t \t - Points of interest: {dist_pois}m")
print("Please be patient, this might take a while!")

### IMPORT NETWORK EDGES
edges = gpd.read_file(study_path)

### LAYER GROUPING

# Remove layers from project if they exist already
remove_existing_layers(
    [
        "Network",
        "To verify",
        "Network in to verify areas",
        "Network in agricultural areas",
        "Agricultural areas",
        "Network in nature areas",
        "Nature areas",
        "Network in culture areas",
        "Culture areas",
        "Network in summer house areas",
        "Summer house areas",
        "Facilities",
        "Facilities within reach",
        "Facilities outside reach",
        "Services",
        "Services within reach",
        "Services outside reach",
        "POIS",
        "POIS within reach",
        "POIS outside reach",
    ]
)

# define root
root = QgsProject.instance().layerTreeRoot()

# make main group for layers
main_group_name = "Evaluate network"

# Check if group already exists
for group in [child for child in root.children() if child.nodeType() == 0]:
    if group.name() == main_group_name:
        root.removeChildNode(group)

# Initialize list of layers for layer grouping
input_layers = []
output_layers = []

if display_input:
    vlayer_network = QgsVectorLayer(study_path, "Network", "ogr")

    QgsProject.instance().addMapLayer(vlayer_network)
    draw_simple_line_layer("Network", color="black", line_width=0.5, line_style="dash")

    zoom_to_layer("Network")

    input_layers.append("Network")

#### **** EVALUATE POLYGON LAYERS **** ####

res = {}  # initialize stats results dictionary

#### AGRICULTURE ####

if os.path.exists(eval_path + "agriculture.gpkg"):
    agri_input_name, agri_output_name, res_agriculture = evaluate_export_plot_poly(
        input_fp=eval_path + "agriculture.gpkg",
        output_fp=results_path + f"agriculture_network_{dist_agri}.gpkg",
        network_edges=edges,
        dist=dist_agri,
        name="Agricultural",
        type_col="types",
        fill_color_rgb=colors["agriculture"],
        outline_color_rgb=colors["agriculture"],
        line_color_rgb=colors["agriculture"],
        line_width=1,
        line_style="solid",
        plot_categorical=False,
        fill_alpha="100",
        outline_alpha="200",
        display_output=display_output,
        display_input=display_input,
    )

    input_layers.append(agri_input_name)
    output_layers.append(agri_output_name)
    res = res | res_agriculture

#### VERIFY #####

if os.path.exists(eval_path + "verify.gpkg"):
    veri_input_name, veri_output_name, res_veri = evaluate_export_plot_poly(
        input_fp=eval_path + "verify.gpkg",
        output_fp=results_path + f"verify_network_{dist_veri}.gpkg",
        network_edges=edges,
        dist=dist_veri,
        name="To verify",
        type_col="types",
        fill_color_rgb=colors["verify"],
        outline_color_rgb=colors["verify"],
        line_color_rgb=colors["verify"],
        line_width=1,
        line_style="solid",
        plot_categorical=False,
        fill_alpha="100",
        outline_alpha="200",
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_veri
    input_layers.append(veri_input_name)
    output_layers.append(veri_output_name)

#### CULTURE ####

if os.path.exists(eval_path + "culture.gpkg"):
    culture_input_name, culture_output_name, res_culture = evaluate_export_plot_poly(
        input_fp=eval_path + "culture.gpkg",
        output_fp=results_path + f"culture_network_{dist_culture}.gpkg",
        network_edges=edges,
        dist=dist_culture,
        name="Culture",
        type_col="types",
        fill_color_rgb=colors["culture"],
        outline_color_rgb="86,85,211",
        line_color_rgb="86,85,211",
        line_width=1,
        line_style="solid",
        plot_categorical=False,
        fill_alpha="100",
        outline_alpha="200",
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_culture
    input_layers.append(culture_input_name)
    output_layers.append(culture_output_name)

#### NATURE ####

if os.path.exists(eval_path + "nature.gpkg"):
    nature_input_name, nature_output_name, res_nature = evaluate_export_plot_poly(
        input_fp=eval_path + "nature.gpkg",
        output_fp=results_path + f"nature_network_{dist_nature}.gpkg",
        network_edges=edges,
        dist=dist_nature,
        name="Nature",
        type_col="types",
        fill_color_rgb=colors["nature"],
        outline_color_rgb=colors["nature"],
        line_color_rgb=colors["nature"],
        line_width=1,
        line_style="solid",
        plot_categorical=False,
        fill_alpha="100",
        outline_alpha="200",
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_nature
    input_layers.append(nature_input_name)
    output_layers.append(nature_output_name)

#### SOMMERHUS ####

if os.path.exists(eval_path + "sommerhus.gpkg"):
    summer_input_name, summer_output_name, res_sommerhus = evaluate_export_plot_poly(
        input_fp=eval_path + "sommerhus.gpkg",
        output_fp=results_path + f"summer_network_{dist_summer}.gpkg",
        network_edges=edges,
        dist=dist_summer,
        name="Summer house",
        type_col="types",
        fill_color_rgb=colors["sommerhus"],
        outline_color_rgb=colors["sommerhus"],
        line_color_rgb=colors["sommerhus"],
        line_width=1,
        line_style="solid",
        plot_categorical=False,
        fill_alpha="100",
        outline_alpha="200",
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_sommerhus
    input_layers.append(summer_input_name)
    output_layers.append(summer_output_name)

#### **** EVALUATE POINT LAYERS **** ####
# for point layers, whether they are within given distance
# (facilities (in 100m), service (500m), pois (1000m))

#### FACILITIES ####

if os.path.exists(eval_path + "facilities.gpkg"):
    (
        faci_input,
        faci_output_within,
        faci_output_outside,
        res_facilities,
    ) = evaluate_export_plot_point(
        input_fp=eval_path + "facilities.gpkg",
        within_reach_output_fp=results_path
        + f"facilities_within_reach_{dist_faci}.gpkg",
        outside_reach_output_fp=results_path
        + f"facilities_outside_reach_{dist_faci}.gpkg",
        network_edges=edges,
        dist=dist_faci,
        name="Facilities",
        type_col="type",
        input_color_rgb=colors["facilities"],
        output_color_reached=colors["facilities"],
        output_color_not_reached=colors["facilities_outside"],
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_facilities
    input_layers.append(faci_input)
    output_layers.append(faci_output_within)
    output_layers.append(faci_output_outside)


#### SERVICE ####
if os.path.exists(eval_path + "service.gpkg"):
    (
        service_input,
        service_output_within,
        service_output_outside,
        res_service,
    ) = evaluate_export_plot_point(
        input_fp=eval_path + "service.gpkg",
        within_reach_output_fp=results_path + f"service_within_reach_{dist_serv}.gpkg",
        outside_reach_output_fp=results_path
        + f"service_outside_reach_{dist_serv}.gpkg",
        network_edges=edges,
        dist=dist_faci,
        name="Services",
        type_col="type",
        input_color_rgb=colors["service"],
        output_color_reached=colors["service"],
        output_color_not_reached=colors["service_outside"],
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_service
    input_layers.append(service_input)
    output_layers.append(service_output_within)
    output_layers.append(service_output_outside)

#### POIS ####
if os.path.exists(eval_path + "pois.gpkg"):
    (
        pois_input,
        pois_output_within,
        pois_output_outside,
        res_pois,
    ) = evaluate_export_plot_point(
        input_fp=eval_path + "pois.gpkg",
        within_reach_output_fp=results_path + f"pois_within_reach_{dist_pois}.gpkg",
        outside_reach_output_fp=results_path + f"pois_outside_reach_{dist_pois}.gpkg",
        network_edges=edges,
        dist=dist_pois,
        name="POIS",
        type_col="type",
        input_color_rgb=colors["pois"],
        output_color_reached=colors["pois"],
        output_color_not_reached=colors["pois_outside"],
        display_output=display_output,
        display_input=display_input,
    )

    res = res | res_pois
    input_layers.append(pois_input)
    output_layers.append(pois_output_within)
    output_layers.append(pois_output_outside)

### SAVE RESULTS OF SUMMARY STATISTICS
with open(f"{stats_path}stats_evaluation.json", "w") as opened_file:
    json.dump(res, opened_file, indent=6)

### VISUALIZATION

all_layers = input_layers + output_layers

types = [
    "Culture",
    "Nature",
    "Agricultural",
    "To verify",
    "POIS",
    "Service",
    "Facilities",
    "Summer",
]

### MAKE MAIN LAYER GROUP
if display_input or display_output:
    main_group = root.insertGroup(0, main_group_name)

for t in types:
    if display_input == False and display_output == True:
        layer_names = [o for o in output_layers if t in o or t.lower() in o]

        sub_group = main_group.addGroup(t)

        for layer_name in layer_names:
            add_layer_to_group(layer_name, sub_group)

    if display_input == True and display_output == False:
        layer_names = [o for o in input_layers if t in o or t.lower() in o]

        sub_group = main_group.addGroup(t)

        add_layer_to_group("Network", main_group)

        for layer_name in layer_names:
            add_layer_to_group(layer_name, sub_group)

    if display_input == True and display_output == True:
        layer_names = [o for o in all_layers if t in o or t.lower() in o]

        sub_group = main_group.addGroup(t)

        add_layer_to_group("Network", main_group)

        for layer_name in layer_names:
            add_layer_to_group(layer_name, sub_group)


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

print("04_evaluate_network script ended successfully \n")
