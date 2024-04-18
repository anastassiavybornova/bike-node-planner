import os
import sys
import yaml
import json
import geopandas as gpd
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
exec(open(homepath + "/src/stat_func.py").read())

# load configs
config_display = yaml.load(
    open(homepath + "/config-display.yml"), Loader=yaml.FullLoader
)
display_slope = config_display["display_slope"]

config_slope = yaml.load(open(homepath + "/config-slope.yml"), Loader=yaml.FullLoader)
segment_length = config_slope["segment_length"]
slope_ranges = config_slope["slope_ranges"]
slope_threshold = slope_ranges[-1]

config_color = yaml.load(
    open(homepath + "/config-colors-slope.yml"), Loader=yaml.FullLoader
)
if "slope" in config_color:
    slope_colors = [v for v in config_color["slope"].values()]
else:
    slope_colors = ["255, 186, 186", "255, 82, 82", "255, 0, 0", "167, 0, 0"]
slope_colors = [rgb2hex(c) for c in slope_colors]

# make output folder
os.makedirs(homepath + "/data/output/elevation/", exist_ok=True)

#### PATHS

# input
edges_fp = homepath + "/data/input/network/processed/edges_studyarea.gpkg"
dem_fp = homepath + "/data/input/dem/dem.tif"

# output
segments_fp = homepath + "/data/output/elevation/segments.gpkg"
elevation_vals_segments_fp = (
    homepath + "/data/output/elevation/elevation_values_edges.gpkg"
)
segments_slope_fp = homepath + "/data/output/elevation/segments_slope.gpkg"
edges_slope_fp = homepath + "/data/output/elevation/edges_slope.gpkg"
steep_segments_fp = homepath + "/data/output/elevation/steep_segments.gpkg"
stats_path = homepath + "/results/stats/stats_slope.json"

if os.path.exists(dem_fp):

    # print out user settings
    print("script04.py started with user settings:")
    print(f"\t Maximal segment length: {segment_length}m")
    print(f"\t Display slope: {display_slope}")
    print(f"\t Slope threshold: {slope_threshold}% (percent)")
    print("Please be patient, this might take a while!")
    print(f"If the script fails to complete, please try again!")

    ##### IMPORT STUDY AREA EDGES AS GDF
    edges = gpd.read_file(edges_fp)
    assert len(edges) == len(edges.edge_id.unique()), "Error: Edge ids are not unique"

    # ##### IMPORT STUDY AREA EDGES AS QGIS LAYER
    vlayer_edges = QgsVectorLayer(edges_fp, "Network edges", "ogr")

    # ##### IMPORT DIGITAL ELEVATION MODEL AS QGIS LAYER
    remove_existing_layers(["DEM terrain"])

    dem_terrain = QgsRasterLayer(dem_fp, "DEM terrain")
    QgsProject.instance().addMapLayer(dem_terrain)

    # ##### GET SLOPE FOR EDGE SEGMENTS

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
    segments_temp_layer.dataProvider().addAttributes(
        [QgsField("segment_id", QVariant.Int)]
    )
    segments_temp_layer.updateFields()
    fld_idx = segments_temp_layer.fields().lookupField("segment_id")
    atts_map = {ft.id(): {fld_idx: ft.id()} for ft in segments_temp_layer.getFeatures()}
    segments_temp_layer.dataProvider().changeAttributeValues(atts_map)
    print("all good")

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

    if display_slope:
        remove_existing_layers(["Segments slope"])

        QgsProject.instance().addMapLayer(vlayer_slope)

        draw_slope_layer(
            layer_name="Segments slope",
            slope_ranges=slope_ranges,
            slope_colors=slope_colors,
            slope_field="slope",
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

    if display_slope:

        remove_existing_layers(["Edges average slope"])

        vlayer_edge_slope = QgsVectorLayer(
            edges_slope_fp,
            "Edges average slope",
            "ogr",
        )

        QgsProject.instance().addMapLayer(vlayer_edge_slope)

        draw_slope_layer(
            layer_name="Edges average slope",
            slope_ranges=slope_ranges,
            slope_colors=slope_colors,
            slope_field="ave_slope",
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
    with open(stats_path, "w") as opened_file:
        json.dump(res, opened_file, indent=6)

    # ##### PLOT RESULTS (STEEP SEGMENTS)

    if display_slope:

        remove_existing_layers(["Segments with slope"])

        vlayer_steep_segments = QgsVectorLayer(
            steep_segments_fp,
            f"Segments with slope > {slope_threshold}%",
            "ogr",
        )

        QgsProject.instance().addMapLayer(vlayer_steep_segments)

        draw_simple_line_layer(
            f"Segments with slope > {slope_threshold}%",
            color="#a70000",
            line_width=1.5,
            line_style="solid",
        )

    group_layers(
        group_name="Slope",
        layer_names=[
            "DEM terrain",
            "Edges average slope",
            "Segments slope",
            f"Segments with slope > {slope_threshold}%",
        ],
        remove_group_if_exists=True,
    )

    print(f"Maximum slope is {segs.slope.max():.2f} %")
    print(f"Average slope is {segs.slope.mean():.2f} %")

    layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

    if "Basemap" in layer_names:
        move_basemap_back(basemap_name="Basemap")

    print("script03.py ended successfully.")
else:
    print("No DEM input file found, skipping slope evaluation.")
    print(
        "Please provide an input file dem.tif in the data/input/dem folder if you want to evaluate the network slope."
    )
