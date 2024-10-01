import os
from owslib.wfs import WebFeatureService
from qgis.core import QgsVectorLayer
from qgis import processing

def fix_geometries(input_layer):
    """
    Fix invalid geometries in input layer and return temporary layer with valid geoms

    Arguments:
        input_layer (vector layer): layer with (potentially) invalid geoms

    Returns:
        fixed_layer: vector layer with valid geoms
    """

    fixed_layer = processing.run(
        "native:fixgeometries", {"INPUT": input_layer, "OUTPUT": "TEMPORARY_OUTPUT"}
    )["OUTPUT"]

    return fixed_layer

def clip_save_layer(input_layer, study_area_vlayer, filepath, layer_name):
    """
    Clip input layer with vector layer and save as geopackage

    Arguments:
        input_layer (vector layer): layer to be clipped
        study_area_vlayer (vector layer): vector layer defining clip extent
        filepath (str): filepath for saving clipped layer
        layer_name (str): name of layer for print statement

    Returns:
        None
    """
    clip_params = {
        "INPUT": input_layer,
        "OVERLAY": study_area_vlayer,
        "OUTPUT": filepath,
    }

    # clip to study area polygon
    processing.run("native:clip", clip_params)

    print(f"Saved layer {layer_name}")

    return None

def get_wfs_layers(
    study_area_vlayer, bounds, wfs_core, wfs_name, wfs_version, homepath, proj_crs
):
    """
    - creates a new subdir for WFS connection
    - downloads all available layers from the WFS connection
    - clips all layers to the extent of study area
    - saves all layers to new directory as geopackage

    Arguments:
        study_area_vlayer (vector layer): vector layer defining the study area/clip extent
        bounds (tuple): bounds for WFS request
        wfs_core (str): base url for WFS connection. E.g. f"https://rida-services.test.septima.dk/ows?MAP={wfs_name}&service=WFS"
        wfs_name (str): name of WFS used to create new directory for storing data (usually same as the name used in the base WFS url)
        wfs_version (str): version of WFS for WFS request
        homepath (str): homepath for QGIS project
        proj_crs (str): CRS in the format "EPSG:XXXX" used for WFS request

    Returns:
        None
    """

    # define bounds
    minx, miny, maxx, maxy = bounds

    # define WFS URL
    wfs_url_get = wfs_core + "&request=GetCapabilities"
    wfs = WebFeatureService(url=wfs_url_get, version=wfs_version)

    layers_to_import = list(wfs.contents)

    print("Importing layers:", layers_to_import, "from WFS: ", wfs_name)

    wfs_dir = homepath + f"/data/raw/wfs/"

    if not os.path.isdir(wfs_dir):
        os.mkdir(wfs_dir)

    wfs_layer_dir = homepath + f"/data/raw/wfs/{wfs_name}/"

    if not os.path.isdir(wfs_layer_dir):
        os.mkdir(wfs_layer_dir)

    for layer in layers_to_import:
        filepath = wfs_layer_dir + layer + ".gpkg"

        print("Getting data for layer:", layer)

        wfs_url = (
            wfs_core
            + f"&request=GetFeature&typeName={layer}&SRSName=EPSG:25832&BBOX={minx},{miny},{maxx},{maxy}"
        )

        Source = f"pagingEnabled='true' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname={proj_crs} typename={layer} url={wfs_url} version='auto'"

        # initialize vector layer of WFS features
        temp_layer = QgsVectorLayer(Source, layer, "WFS")

        fixed_layer = fix_geometries(temp_layer)

        clip_save_layer(fixed_layer, study_area_vlayer, filepath, layer)