import numpy as np
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import shapely

# from shapely.geometry import Point
# from shapely.wkt import loads, dumps
import momepy

# import networkx as nx
# import json
from shapely.ops import linemerge
from shapely.geometry import LineString, Point
import osmnx as ox


def unzip_linestrings(org_gdf, edge_id_col):
    """
    Splits lines into their smallest possible line geometry, so each line only is defined by the start and end coordinate.
    Used to convert reference data to a similar data structure as used by osnmnx

    Arguments:
        org_gdf (gdf): gdf with original linestring/multilinestring data
        edge_id_col (str): name of column in org_gdf with unique edge id

    Returns:
        new_gdf (gdf): gdf with smallest possible linestring, with the same attributes as the original
    """

    gdf = org_gdf.copy()

    gdf["geometry"] = gdf["geometry"].apply(
        lambda x: linemerge(x) if x.geom_type == "MultiLineString" else x
    )

    # helper column: list of points
    gdf["points"] = gdf.apply(lambda x: [c for c in x.geometry.coords], axis=1)
    gdf["edges"] = gdf.apply(
        lambda x: [LineString(e) for e in zip(x.points, x.points[1:])], axis=1
    )
    edgelist = [item for sublist in gdf["edges"] for item in sublist]

    gdf[edge_id_col] = gdf.apply(lambda x: len(x.edges) * [x[edge_id_col]], axis=1)

    edgeid_list = [item for sublist in gdf[edge_id_col] for item in sublist]

    new_gdf = gpd.GeoDataFrame(
        {"geometry": edgelist, edge_id_col: edgeid_list}, crs=org_gdf.crs
    )

    new_gdf["new_edge_id"] = new_gdf.index  # Create random but unique edge id!
    assert len(new_gdf) == len(new_gdf.new_edge_id.unique())

    new_gdf = new_gdf.merge(
        org_gdf.drop("geometry", axis=1), how="left", on=edge_id_col
    )

    return new_gdf


def create_osmnx_graph(gdf):
    """
    Function for  converting a geodataframe with LineStrings to a NetworkX graph object (MultiDiGraph), which follows the data structure required by OSMnx.
    (I.e. Nodes indexed by osmid, nodes contain columns with x and y coordinates, edges is multiindexed by u, v, key).
    Converts MultiLineStrings to LineStrings - assumes that there are no gaps between the lines in the MultiLineString

    OBS! Current version does not fix issues with topology.

    Arguments:
        gdf (gdf): The data to be converted to a graph format
        directed (bool): Whether the resulting graph should be directed or not. Directionality is based on the order of the coordinates.

    Returns:
        G_ox (NetworkX MultiDiGraph object): The original data in a NetworkX graph format
    """

    gdf["geometry"] = gdf["geometry"].apply(
        lambda x: linemerge(x) if x.geom_type == "MultiLineString" else x
    )

    # If Multilines cannot be merged do to gaps, use explode
    geom_types = gdf.geom_type.to_list()
    # unique_geom_types = set(geom_types)

    if "MultiLineString" in geom_types:
        gdf = gdf.explode(index_parts=False)

    G = momepy.gdf_to_nx(gdf, approach="primal", directed=True)

    nodes, edges = momepy.nx_to_gdf(G)

    # Create columns and index as required by OSMnx
    # index_length = len(str(nodes['nodeID'].iloc[-1].item()))
    nodes["osmid"] = nodes[
        "nodeID"
    ]  # .apply(lambda x: create_node_index(x, index_length))

    # Create x y coordinate columns
    nodes["x"] = nodes.geometry.x
    nodes["y"] = nodes.geometry.y

    edges["u"] = nodes["osmid"].loc[edges.node_start].values
    edges["v"] = nodes["osmid"].loc[edges.node_end].values

    nodes.set_index("osmid", inplace=True)

    edges["length"] = edges.geometry.length  # Length is required by some functions

    edges["key"] = 0

    edges = find_parallel_edges(edges)

    # Create multiindex in u v key format
    edges = edges.set_index(["u", "v", "key"])

    # For ox simplification to work, edge geometries must be dropped. Edge geometries is defined by their start and end node
    # edges.drop(['geometry'], axis=1, inplace=True) # Not required by new simplification function

    G_ox = ox.graph_from_gdfs(nodes, edges)

    return G_ox


def find_parallel_edges(edges):
    """
    Check for parallel edges in a pandas DataFrame with edges, including columns u with start node index and v with end node index.
    If two edges have the same u-v pair, the column 'key' is updated to ensure that the u-v-key combination can uniquely identify an edge.
    Note that (u,v) is not considered parallel to (v,u)

    Arguments:
        edges (gdf): network edges

    Returns:
        edges (gdf): edges with updated key index
    """

    # Find edges with duplicate node pairs
    parallel = edges[edges.duplicated(subset=["u", "v"])]

    edges.loc[parallel.index, "key"] = 1  # Set keys to 1

    k = 1

    while len(edges[edges.duplicated(subset=["u", "v", "key"])]) > 0:
        k += 1

        parallel = edges[edges.duplicated(subset=["u", "v", "key"])]

        edges.loc[parallel.index, "key"] = k  # Set keys to 1

    assert (
        len(edges[edges.duplicated(subset=["u", "v", "key"])]) == 0
    ), "Edges not uniquely indexed by u,v,key!"

    return edges


def order_edge_nodes(edges):
    for index, row in edges.iterrows():
        org_u = row.u
        org_v = row.v

        edges.loc[index, "u"] = min(org_u, org_v)
        edges.loc[index, "v"] = max(org_u, org_v)


def assign_edges_start_end_nodes(edges, nodes):
    """
    Assign node ids of start and end nodes for edges in an edge geodataframe, based on the closest nodes in a node geodataframe

    Arguments:
        edges (gdf): network edges
        nodes (gdf): network nodes

    Returns:
        edges (gdf): edges with u column with start node id and v column with end node id
    """

    # Extract start and end coordinates of each linestring
    first_coord = edges["geometry"].apply(lambda g: Point(g.coords[0]))
    last_coord = edges["geometry"].apply(lambda g: Point(g.coords[-1]))

    # Add start and end as columns to the gdf
    edges["start_coord"] = first_coord
    edges["end_coord"] = last_coord

    start_coords = edges[["edge_id", "start_coord"]].copy()
    start_coords.set_geometry("start_coord", inplace=True, crs=edges.crs)

    end_coords = edges[["edge_id", "end_coord"]].copy()
    end_coords.set_geometry("end_coord", inplace=True, crs=edges.crs)

    # join start and end coors to nearest node
    start_joined = start_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]], how="left", distance_col="distance"
    )
    end_joined = end_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]], how="left", distance_col="distance"
    )

    edges.drop(["start_coord", "end_coord"], axis=1, inplace=True)

    # Merge with edges
    edges = edges.merge(
        start_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    edges.rename({"node_id": "u"}, inplace=True, axis=1)

    edges = edges.merge(
        end_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    edges.rename({"node_id": "v"}, inplace=True, axis=1)

    return edges


# ### function that converts a networkx graph in osmnx format to a json file
# def spatialgraph_tojson(G, my_crs, filepath):
#     # copy graph
#     G = G.copy()

#     # convert crs to string to make it json serializable
#     my_crs_string = str(my_crs)

#     # json serialization
#     node_link_data = nx.node_link_data(G)

#     # add crs from string
#     node_link_data[
#         "graph"
#     ] = (
#         {}
#     )  # step needed to delete the "crs type" object from here and overwrite it with a str object
#     node_link_data["graph"]["crs"] = my_crs_string

#     # replace each linestring by its string representation
#     for linkdict in node_link_data["links"]:
#         if "geometry" in linkdict.keys():
#             linkdict["geometry"] = dumps(linkdict["geometry"])

#     # replace each linestring by its string representation
#     for nodedict in node_link_data["nodes"]:
#         if "geometry" in nodedict.keys():
#             nodedict["geometry"] = dumps(nodedict["geometry"])

#     with open(filepath, "w") as f:
#         json.dump(node_link_data, f)

#     print(f"json serialized graph saved to {filepath}")


# ### function that reads in a json file into a networkx object
# def spatialgraph_fromjson(filepath):
#     node_link_data = json.load(open(filepath))

#     # load geometries from wkt
#     for linkdict in node_link_data["links"]:
#         if "geometry" in linkdict.keys():
#             linkdict["geometry"] = loads(linkdict["geometry"])

#     # load geometries from wkt
#     for nodedict in node_link_data["nodes"]:
#         if "geometry" in nodedict.keys():
#             nodedict["geometry"] = loads(nodedict["geometry"])

#     # convert node link data into nx graph object
#     G = nx.node_link_graph(node_link_data)

#     return G


# ### convert a geodataframe of linestrings into a networkx graph
# def get_graph_from_gdf(gdf):
#     # get "noded" gdf
#     n = shapely.node(gdf.unary_union)
#     n = gpd.GeoDataFrame({"geometry": [n]}, crs=gdf.crs)
#     n = n.explode().reset_index(drop=True)  # index_parts=False
#     n["id"] = n.index

#     # make graph
#     Gdir = momepy.gdf_to_nx(n, multigraph=False)
#     G = Gdir.to_undirected()
#     print("comps:", len([c for c in nx.connected_components(G)]))
#     print("degrees:", nx.degree_histogram(G))

#     return G


# def get_node_gdf(G, return_degrees=True):
#     mycrs = G.graph["crs"]

#     # get nodes gdf
#     nodes = gpd.GeoDataFrame(
#         {"geometry": [Point(node) for node in G.nodes], "id": list(G.nodes)}, crs=mycrs
#     )

#     # add degree info
#     if return_degrees == True:
#         nodes["degree"] = nodes.apply(lambda x: G.degree(x.id), axis=1)

#     return nodes


# def get_edge_gdf(G, return_components=True):
#     mycrs = G.graph["crs"]

#     # get edge gdf
#     geomdict = nx.get_edge_attributes(G, "geometry")

#     edges = gpd.GeoDataFrame(
#         {"geometry": geomdict.values(), "id": geomdict.keys()}, crs=mycrs
#     )

#     if return_components == True:
#         comps = [c for c in nx.connected_components(G)]

#         edges["component_nr"] = None

#         for i, comp in enumerate(comps):
#             l1 = list(G.edges(comp))

#             # accounting for the edge id indexing mess
#             l2 = [(l[1], l[0]) for l in l1]
#             l = l1 + l2

#             edges.loc[edges["id"].isin(l), "component_nr"] = i

#     return edges


# ##########
