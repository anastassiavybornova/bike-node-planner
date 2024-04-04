##### CUSTOM SETTINGS FOR DISPLAY (type either False or True)
plot_intermediate = True
plot_results = True

##### NO CHANGES BELOW THIS LINE

### SETUP

# import python packages
import os

os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
from owslib.wms import WebMapService
import geopandas as gpd
import yaml
import json

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# import plotting functions
exec(open(homepath + "/src/plot_func.py").read())
exec(open(homepath + "/src/stat_func.py").read())

# load configs and colors
configfile = os.path.join(homepath, "config.yml")  # filepath of config file
configs = yaml.load(open(configfile), Loader=yaml.FullLoader)
proj_crs = configs["proj_crs"]
dataforsyning_token = configs["dataforsyning_token"]
sa_name = configs["study_area_name"]
segment_length = configs["segment_length"]
slope_threshold = configs["slope_ranges"][-1]

colorfile = os.path.join(homepath, "colors.yml")  # filepath of config file
colors = yaml.load(open(colorfile), Loader=yaml.FullLoader)
slope_colors = [
    colors["slope_0"], 
    colors["slope_a"], 
    colors["slope_b"], 
    colors["slope_c"]
    ]
slope_colors = [rgb2hex(c) for c in slope_colors]

#### PATHS

# input
edges_fp = homepath + "/data/processed/workflow_steps/network_edges_no_parallel.gpkg"
dem_fp = homepath + f"/data/processed/workflow_steps/merged_dem_{sa_name}.tif"

# output
elevation_vals_segments_fp = (
    homepath + "/data/processed/workflow_steps/elevation_values_segments.gpkg"
)
elevation_vals_edges_fp = (
    homepath + "/data/processed/workflow_steps/elevation_values_edges.gpkg"
)
segments_fp = homepath + "/data/processed/workflow_steps/segments.gpkg"

segments_slope_fp = homepath + "/results/data/segments_slope.gpkg"
edges_slope_fp = homepath + "/results/data/edges_slope.gpkg"
steep_segments_fp = homepath + "/results/data/very_steep_segments.gpkg"
results_path = homepath + "/results/data/"  # store output geopackages here
stats_path = homepath + "/results/stats/"  # store output json here

# print out user settings
print("05_compute_slope script started with user settings:")
print(f"\t Maximal segment length: {segment_length}m")
print(f"\t Plot intermediate results: {plot_intermediate}")
print(f"\t Plot final results: {plot_results}")
print(f"\t Slope threshold: {slope_threshold}% (percent)")
print("Please be patient, this might take a while!")
print(f"If the script fails to complete, please try again!")

##### IMPORT STUDY AREA EDGES AS GDF
edges = gpd.read_file(edges_fp)
assert len(edges) == len(edges.edge_id.unique())

#### PREPARE THE DIGITAL ELEVATION MODEL

if os.path.exists(dem_fp) == False:
    exec(open(homepath + "/src/download_dem.py").read())
    exec(open(homepath + "/src/merge_dem.py").read())

#### REMOVE EXISTING LAYERS

remove_existing_layers(
    [
        "Network edges",
        "Split",
        "Segments",
        "Vertices",
        "Elevation values",
        "dhm_terraen_skyggekort",
        "dem_terrain",
        "Segments slope",
        "Edges average slope",
        "Very steep segments",
    ]
)

##### IMPORT STUDY AREA EDGES AS QGIS LAYER
vlayer_edges = QgsVectorLayer(edges_fp, "Network edges", "ogr")


if plot_intermediate:
    QgsProject.instance().addMapLayer(vlayer_edges)

    draw_simple_line_layer(
        "Network edges", color="black", line_width=1, line_style="solid"
    )

##### IMPORT DIGITAL ELEVATION MODEL AS QGIS LAYER
dem_terrain = QgsRasterLayer(dem_fp, "dem_terrain")

##### PLOT TERRAIN
if plot_intermediate:
    QgsProject.instance().addMapLayer(dem_terrain)

##### PLOT HILLSHADE
if plot_intermediate and dataforsyning_token:
    dem_name = "dhm_terraen_skyggekort"
    wms_url = "https://api.dataforsyningen.dk/dhm_DAF?" + f"token={dataforsyning_token}"
    source = f"crs={proj_crs}&dpiMode=7&format=image/png&layers={dem_name}&styles&tilePixelRatio=0&url={wms_url}"

    dem_raster = QgsRasterLayer(source, dem_name, "wms")

    QgsProject.instance().addMapLayer(dem_raster)

    print("added dem raster")

##### GET SLOPE FOR EDGE SEGMENTS

# segmentize
line_segments = processing.run(
    "native:splitlinesbylength",
    {"INPUT": vlayer_edges, "LENGTH": segment_length, "OUTPUT": "TEMPORARY_OUTPUT"},
)

# delete "fid" field (to prevent problems when exporting a layer with non-unique fields)
segments_temp_layer = line_segments["OUTPUT"]
layer_provider = segments_temp_layer.dataProvider()
fid_idx = segments_temp_layer.fields().indexOf("fid")
segments_temp_layer.dataProvider().deleteAttributes([fid_idx])
segments_temp_layer.updateFields()

# create new unique segment id
segments_temp_layer.dataProvider().addAttributes([QgsField("segment_id", QVariant.Int)])
segments_temp_layer.updateFields()
fld_idx = segments_temp_layer.fields().lookupField("segment_id")
atts_map = {ft.id(): {fld_idx: ft.id()} for ft in segments_temp_layer.getFeatures()}
segments_temp_layer.dataProvider().changeAttributeValues(atts_map)

# export
_writer = QgsVectorFileWriter.writeAsVectorFormat(
    segments_temp_layer,
    segments_fp,
    "utf-8",
    segments_temp_layer.crs(),
    "GPKG",
)

vlayer_segments = QgsVectorLayer(
    segments_fp,
    "Segments",
    "ogr",
)

if plot_intermediate:
    QgsProject.instance().addMapLayer(vlayer_segments)
    draw_simple_line_layer("Segments", color="red", line_width=1, line_style="dash")

print(f"done: line split into segments of max length {segment_length} meters.")

# GET START AND END VERTICES
segment_vertices = processing.run(
    "native:extractspecificvertices",
    {
        "INPUT": vlayer_segments,
        "VERTICES": "0,-1",
        "OUTPUT": "TEMPORARY_OUTPUT",
    },
)

if plot_intermediate:
    QgsProject.instance().addMapLayer(segment_vertices["OUTPUT"])

    vertices = QgsProject.instance().mapLayersByName("Vertices")[0]

    draw_simple_point_layer(
        "Vertices",
        color="0,0,0,180",
        marker_size=1,
        outline_width=0,
    )
print(f"done: extracted segment start and end points")

elevation_values = processing.run(
    "native:rastersampling",
    {
        "INPUT": segment_vertices["OUTPUT"],
        "RASTERCOPY": dem_terrain,
        "COLUMN_PREFIX": "elevation_",
        "OUTPUT": "TEMPORARY_OUTPUT",  # elevation_vals_fp,
    },
)

# export
elevation_temp_layer = elevation_values["OUTPUT"]
# delete "fid" field (to prevent problems when exporting a layer with non-unique fields)
layer_provider = elevation_temp_layer.dataProvider()
fid_idx = elevation_temp_layer.fields().indexOf("fid")
elevation_temp_layer.dataProvider().deleteAttributes([fid_idx])
elevation_temp_layer.updateFields()

_writer = QgsVectorFileWriter.writeAsVectorFormat(
    elevation_temp_layer,
    elevation_vals_segments_fp,
    "utf-8",
    elevation_temp_layer.crs(),
    "GPKG",
)

vlayer_elevation = QgsVectorLayer(
    elevation_vals_segments_fp,
    "Elevation values segments",
    "ogr",
)

if plot_intermediate:
    QgsProject.instance().addMapLayer(vlayer_elevation)
    draw_simple_point_layer(
        "Elevation values segments",
        color="255,0,0,180",
        marker_size=2,
        outline_color="white",
        outline_width=0.2,
    )

ele = gpd.read_file(elevation_vals_segments_fp)
segs = gpd.read_file(segments_fp)

elevation_col = "elevation_1"
grouped = ele.groupby("segment_id")

segs["slope"] = None

for seg_id, group in grouped:
    if len(group) != 2:
        print(f"Error, got {len(group)} row(s)")
    else:
        e1 = group[elevation_col].values[0]
        e2 = group[elevation_col].values[1]
        seg_length = segs.loc[segs.segment_id == seg_id].geometry.length.values[0]

        slope = (e2 - e1) / (seg_length - 0)

        segs["slope"].loc[segs.segment_id == seg_id] = abs(slope) * 100

segs["slope"].fillna(0, inplace=True)

if os.path.exists(segments_slope_fp):
    os.remove(segments_slope_fp)
segs.to_file(segments_slope_fp, mode="w")

###

vlayer_slope = QgsVectorLayer(
    segments_slope_fp,
    "Segments slope",
    "ogr",
)

if plot_results:
    QgsProject.instance().addMapLayer(vlayer_slope)

    draw_slope_layer(
        layer_name="Segments slope", 
        slope_ranges=configs["slope_ranges"],
        slope_colors=slope_colors,
        slope_field="slope"
        )

### GET MIN MAX AVE SLOPE FOR EDGES (BASED ON EDGE SEGMENTS) ######

edges["min_slope"] = 0
edges["max_slope"] = 0
edges["ave_slope"] = 0

grouped = segs.groupby("edge_id")

for edge_id, group in grouped:
    min_slope = group["slope"].min()
    max_slope = group["slope"].max()
    ave_slope = group["slope"].mean()

    edges["min_slope"].loc[edges.edge_id == edge_id] = min_slope
    edges["max_slope"].loc[edges.edge_id == edge_id] = max_slope
    edges["ave_slope"].loc[edges.edge_id == edge_id] = ave_slope

##### EXPORT RESULTS (SLOPE BY EDGE)
if os.path.exists(edges_slope_fp):
    os.remove(edges_slope_fp)
edges.to_file(edges_slope_fp, mode="w")

##### PLOT RESULTS (SLOPE BY EDGE)

if plot_results:
    vlayer_edge_slope = QgsVectorLayer(
        edges_slope_fp,
        "Edges average slope",
        "ogr",
    )

    QgsProject.instance().addMapLayer(vlayer_edge_slope)

    draw_slope_layer(
        layer_name="Edges average slope", 
        slope_ranges=configs["slope_ranges"],
        slope_colors=slope_colors,
        slope_field="ave_slope"
        )

steep_segments = segs.loc[segs.slope > slope_threshold]
if os.path.exists(steep_segments_fp):
    os.remove(steep_segments_fp)
steep_segments.to_file(steep_segments_fp, mode="w")

### Save summary statistics of slope computation
res = {}  # initialize stats results dictionary
res["segs_length"] = list(segs["length"])
res["segs_slope"] = list(segs["slope"])
res["segs_slope_min"] = segs.slope.min()
res["segs_slope_max"] = segs.slope.max()
res["segs_slope_mean"] = segs.slope.mean()
with open(f"{stats_path}stats_slope.json", "w") as opened_file:
    json.dump(res, opened_file, indent=6)

##### PLOT RESULTS (STEEP SEGMENTS)

if plot_results:
    vlayer_steep_segments = QgsVectorLayer(
        steep_segments_fp,
        "Very steep segments",
        "ogr",
    )

    QgsProject.instance().addMapLayer(vlayer_steep_segments)

    draw_simple_line_layer(
        "Very steep segments",
        color="#a70000",
        line_width=1.5,
        line_style="solid",
    )


if plot_intermediate and plot_results:
    group_layers(
        "Compute network slope",
        [
            "dhm_terraen_skyggekort",
            "dem_terrain",
            "Network edges",
            "Segments",
            "Vertices",
            "Edges average slope",
            "Segments slope",
            "Elevation values segments",
            "Very steep segments",
        ],
        remove_group_if_exists=True,
    )

if plot_results and not plot_intermediate:
    group_layers(
        "Compute network slope",
        [
            "Edges average slope",
            "Segments slope",
        ],
        remove_group_if_exists=True,
    )

if plot_intermediate and not plot_results:
    group_layers(
        "Compute network slope",
        [
            "dhm_terraen_skyggekort",
            "dem_terrain",
            "Network edges",
            "Segments",
            "Vertices",
            "Elevation values segments",
            "Very steep segments",
        ],
        remove_group_if_exists=True,
    )


print(f"Maximum slope is {segs.slope.max():.2f} %")
print(f"Average slope is {segs.slope.mean():.2f} %")


layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

turn_off_layer_names = [
    "Elevation values segments",
    "Vertices",
    "Segments",
    "Network edges",
]

turn_off_layer_names = [t for t in turn_off_layer_names if t in layer_names]

turn_off_layers(turn_off_layer_names)

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

print("05_compute_slope script ended successfully \n")
