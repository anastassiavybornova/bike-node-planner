# Step 02: Prepare your input data 

## If your study area is in Denmark

For all Danish municipalities, the steps below (how to provide input data for the BikeNodePlanner) have been **automatized**. Disregard all steps below; instead, find detailed instructions on how to automatically generate input data for your Danish study area [here](https://github.com/anastassiavybornova/bike-node-planner-data-denmark).

## Format and provide data

All files must be in the **GeoPackage file format**, readable by [GeoPandas](https://geopandas.org/en/stable/docs/user_guide/io.html) and by [QGIS](https://docs.qgis.org/3.28/en/docs/user_manual/managing_data_source/opening_data.html). 

All data must be in the same **projected coordinate reference system**.

To provide the necessary input data, navigate to the `bike-node-planner-main` folder on your local machine. (See previous step for instructions on how to download the folder from GitHub.) 

All data sets described below need to be placed in the corresponding subfolders of `bike-node-planner-main/data/input/`.

## Provide study area polygon

To provide the study area, place this 1 file in the `studyarea` subfolder:

1. `studyarea.gpkg`: 

a single **polygon or multipolygon** delineating the extent of the study area.  

## Provide network data

To provide input network data, place these 2 files in the `/network/communication/` subfolder:

1. `nodes.gpkg`: a set of point geometries representing the bicycle nodes 
2. `edges.gpkg`: a set of linestring geometries representing the network edges in the bicycle network

* All nodes must have a unique node id and all edges must be uniquely indexed by their start and end node. 
* The network must be simplified: each intersection must be represented by exactly one node, and each network segment must be represented by exactly one edge. **Note:** If your network data is more detailed (e.g. in a format used for routing on the road network or technical planning of signage at intersections), the BikeNodePlanner includes a pre-processing step that can convert the detailed network into the required simplified network; see the last section on this page for instructions, [Simplify network](/docs/step02_prepare_data.md#if-necessary-simplify-network). 
* The network must be topologically correct, i.e. with snapping of edge and node geometries. 
* No parallel edges are allowed, so if more than one edge runs between the same node pair, the edge must be split by adding an interstitial node on one of the parallel edges (even if the edges have different geometries). For example in the illustration below, there are two edges between nodes (1) and (2); hence, the interstitial node (5) needs to be placed on one of the edges.

<p align="center"><img alt="Illustration of interstitial node" src="/img/inter_node.png" width=25%></p>

## Optional: Provide land use data for evaluation (polygon geometries)

This step is fully customizable. You can decide yourself which land use data to use here. The BikeNodePlanner will evaluate the network for each provided land use layer _separately_, analyzing which parts of the network run _through_ each of the land use layers. 

To provide land use data, place at least one file in the `/polygon/` subfolder:

1. `layer1.gpkg`
2. `layer2.gpkg`
3. ...

Each file has to contain a set of polygons for the study area.

Note the the filenames are **customizable**: replace "layer1" by a filename of your choice which describes the layer. For example, you may choose to provide one land use layer containing all nature in your study area (e.g., "nature.gpkg"); or you may choose to provide three layers containing different nature categories, to be analyzed separately (e.g., "forest.gpkg", "seaside.gpkg", "grassland.gpkg"). 

For each polygon layer, you can define a customized buffer distance: how close to the polygon does the network need to run to be counted as "within that polygon layer"? (see [Step 03](/docs/step03_customize_settings.md))

If no data is provided in the `/polygon/` subfolder, the BikeNodePlanner will conduct no polygon layer analysis.

## Optional: Provide points of interest data for evaluation (point geometries)

This step is fully customizable. You can decide yourself which point of interest data to use here. The BikeNodePlanner will evaluate the network for each provided point layer _separately_, analyzing which points are _within_ and which points are _outside_ reach of the network. 

To provide point of interest data, place at least one file in the `/point/` subfolder:

1. `layer1.gpkg`
2. `layer2.gpkg`
3. ...

Each file has to contain a set of points for the study area.

Note the the filenames are **customizable**: replace "layer1" by a filename of your choice which describes the layer. For example, you may choose to provide one land use layer containing all tourist attractions in your study area (e.g., "attractions.gpkg"); or you may choose to provide three layers containing different tourist attraction categories, to be analyzed separately (e.g., "museums.gpkg", "churches.gpkg", "monuments.gpkg"). 

For each point layer, you can define a customized buffer distance: how close to the network does a point need to be to be counted as "within reach"? (see [Step 03](/docs/step03_customize_settings.md))

If no data is provided in the `/point/` subfolder, the BikeNodePlanner will conduct no point layer analysis.

## Optional: Provide elevation data (tif file)

To provide elevation data for the area, place this 1 file in the `/elevation/` subfolder:

1. `dem.tif`

The elevation data set must:

* Cover the entire study area.
* Be in a `.tif` format, readable by QGIS and GeoPandas
* Be in a sufficiently high resolution to compute the slope of the network stretches: a resolution of 10 * 10 meters or higher is recommended.

If no data is provided in the `/dem/` subfolder, the BikeNodePlanner will conduct no elevation analysis.

## If necessary: simplify network

to do: provide here instructions on how to simplify network (cf. https://github.com/anastassiavybornova/knudepunkter/blob/main/docs/datarequirements.md)

***

Illustrations and data specifications based on Septima, 2023 [LINK].