# Step 02: Prepare your input data 

## 🇩🇰 If your study area is in Denmark 🇩🇰

For all Danish municipalities, the steps below (how to provide input data for the BikeNodePlanner) have been **automatized**. Disregard all steps below; instead, find detailed instructions on how to automatically generate input data for your Danish study area [here](https://github.com/anastassiavybornova/bike-node-planner-data-denmark).

## How to format and provide data

You need to provide the following data sets, described in detail below:
* [Study area polygon](/docs/step02_prepare_data.md#study-area-polygon)
* [Network data](/docs/step02_prepare_data.md#network-data) in study area (nodes and edges)
* (Optional) Evaluation data for study area: [polygon layers](/docs/step02_prepare_data.md#optional-land-use-data-for-evaluation-polygon-geometries)
* (Optional) Evaluation data for study area: [point layers](/docs/step02_prepare_data.md#optional-points-of-interest-data-for-evaluation-point-geometries)
* (Optional) Elevation data for study area: [a tif file](/docs/step02_prepare_data.md#optional-elevation-data-tif-file)

### General data requirements

* All files must be in the **GeoPackage file format**, readable by [GeoPandas](https://geopandas.org/en/stable/docs/user_guide/io.html) and by [QGIS](https://docs.qgis.org/3.28/en/docs/user_manual/managing_data_source/opening_data.html). 
* All data must be in the same **projected coordinate reference system**.
* To provide the necessary input data, navigate to the `/bike-node-planner-main/` folder on your local machine. (See [previous step](/README.md#step-1-software-installations) for instructions on how to download the folder from GitHub.)
* All data sets described below need to be placed in the corresponding subfolders of `/bike-node-planner-main/data/input/`.
* Once you run the BikeNodePlanner in QGIS, the first step will automatically make sure that the data sets you provided follow all the specifications (see [Step 04](/docs/step04_run_evaluation.md) for details).

***

## Study area polygon

To provide the study area, place this 1 file in the `studyarea` subfolder:

1. `studyarea.gpkg`: a single **polygon or multipolygon** delineating the extent of the study area.  

***

## Network data

To provide input network data, place these 2 files in the `/network/` subfolder:

1. `nodes.gpkg`: a set of *Point* geometries representing the bicycle nodes.
2. `edges.gpkg`: a set of *LineString* geometries representing the network edges in the bicycle network.

### Requirements

* All nodes must have a unique node id (*"node_id"*) and all edges must have a unique edge id (*"edge_id"*).
* The edge data set must contain three **columns**, *"u","v","key"*, with "u" referencing the id of the edge start node, "v" referencing the id of the edge end node, and "key" containing an integar value from 0 to N to distinguish between edges running between the same start and end node pairs (similar to the data structure used by, for example, [OSMnx](https://osmnx.readthedocs.io/en/stable/user-reference.html#osmnx.utils_graph.graph_from_gdfs)).
* The network must be topologically correct, i.e. with snapping of edge and node geometries.

***

## Optional: Land use data for evaluation (polygon geometries)

This step is fully customizable. You can decide yourself which land use data to use here. The BikeNodePlanner will evaluate the network for each provided land use layer _separately_, analyzing which parts of the network run _through_ each of the land use layers.

To provide land use data, place at least one file in the `/polygon/` subfolder:

1. `polygonlayer1.gpkg`
2. `polygonlayer2.gpkg`
3. ...

### Requirements

* Each file has to contain a set of polygons for the study area.
* Note the the filenames are **customizable**: replace "polygonlayerX.gpkg" by a filename of your choice which describes the layer. For example, you may choose to provide one land use layer containing all nature in your study area (e.g., "nature.gpkg"); or you may choose to provide three layers containing different nature categories, to be analyzed separately (e.g., "forest.gpkg", "seaside.gpkg", "grassland.gpkg"). 
* For each polygon layer, you can define a customized buffer distance: how close to the polygon does the network need to run to be counted as "within that polygon layer"? (see [Step 03](/docs/step03_customize_settings.md))

> **Note:** Providing this data is optional. If no data is provided in the `/polygon/` subfolder, the BikeNodePlanner will conduct no polygon layer analysis.

***

## Optional: Points of interest data for evaluation (point geometries)

This step is fully customizable. You can decide yourself which point of interest data to use here. The BikeNodePlanner will evaluate the network for each provided point layer _separately_, analyzing which points are _within_ and which points are _outside_ reach of the network. 

To provide point of interest data, place at least one file in the `/point/` subfolder:

1. `pointlayer1.gpkg`
2. `pointlayer2.gpkg`
3. ...

### Requirements

* Each file has to contain a set of points for the study area.
* Note the the filenames are **customizable**: replace "pointlayerX.gpkg" by a filename of your choice which describes the layer. For example, you may choose to provide one land use layer containing all tourist attractions in your study area (e.g., "attractions.gpkg"); or you may choose to provide three layers containing different tourist attraction categories, to be analyzed separately (e.g., "museums.gpkg", "churches.gpkg", "monuments.gpkg"). 
* For each point layer, you can define a customized buffer distance: how close to the network does a point need to be to be counted as "within reach"? (see [Step 03](/docs/step03_customize_settings.md))

> **Note:** Providing this data is optional. If no data is provided in the `/point/` subfolder, the BikeNodePlanner will conduct no point layer analysis.

***

## Optional: Elevation data (tif file)

To provide elevation data for the area, place this 1 file in the `/elevation/` subfolder:

1. `dem.tif`

### Requirements 

The elevation data set must:
* Cover the entire study area.
* Be in a `.tif` format, readable by QGIS and GeoPandas
* Be in a sufficiently high resolution to compute the slope of the network stretches: a resolution of 10 * 10 meters or higher is recommended.

> **Note:** Providing this data is optional. If no data is provided in the `/dem/` subfolder, the BikeNodePlanner will conduct no elevation analysis.

***

Illustrations and data specifications based on Septima, 2023 [LINK].