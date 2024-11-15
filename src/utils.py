import os
os.environ["USE_PYGEOS"] = "0"
import re
import shutil
import geopandas as gpd
import pandas as pd
import momepy
import networkx as nx
from shapely.geometry import Point, LineString

### TODO previously: wfs-func.py

### added from https://github.com/anastassiavybornova/knudepunkter/blob/main/src/wfs_func.py


# imports layers from one WFS folder
def addlayers_from_wfsfolder(wfs_dict, wfs_folder, layernames, wfs_path):
    for wfs_layer in layernames:
        wfs_dict[wfs_folder][wfs_layer] = gpd.read_file(
            wfs_path + f"/{wfs_folder}/{wfs_layer}.gpkg"
        ).explode(index_parts=False)
    return wfs_dict


# merges WFS gdfs into one gdf
def merge_gdfs(gdf_list):
    # make sure all gdfs are the same crs
    assert len(set([gdf.crs for gdf in gdf_list])) == 1
    # make sure we have the same geometries everywhere
    assert len(set([t for gdf in gdf_list for t in gdf.type])) == 1
    # concatenate with pandas
    gdf_main = pd.concat([gdf[["geometry", "type"]].copy() for gdf in gdf_list])
    return gdf_main


def get_bounds(gdf):
    # get bounds of geodataframe
    bounds = gdf.bounds
    minx = bounds.minx[0]
    miny = bounds.miny[0]
    maxx = bounds.maxx[0]
    maxy = bounds.maxy[0]

    return minx, miny, maxx, maxy

### TODO previously in generate-input.py

def _drop_multiple_joins(joined_nodes):

    joined_nodes.reset_index(inplace=True)

    v = joined_nodes.edge_id.value_counts()
    grouped = joined_nodes[joined_nodes.edge_id.isin(v.index[v.gt(1)])].groupby(
        "edge_id"
    )

    drop_joined = []
    for edge_id, g in grouped:
        node_id = g.node_id.max()
        drop_joined.append((edge_id, node_id))

    for d in drop_joined:
        joined_nodes.drop(
            joined_nodes[
                (joined_nodes.edge_id == d[0]) & (joined_nodes.node_id == d[1])
            ].index,
            inplace=True,
        )

    return joined_nodes


def assign_edges_start_end_nodes(edges, nodes, max_distance=5):
    """
    Assign node ids of start and end nodes for edges in an edge geodataframe, based on the closest nodes in a node geodataframe

    Arguments:
        edges (gdf): network edges
        nodes (gdf): network nodes

    Returns:
        edges (gdf): edges with u column with start node id and v column with end node id
    """

    # Extract start and end coordinates of each linestring
    first_coord = edges.geometry.apply(lambda g: Point(g.coords[0]))
    last_coord = edges.geometry.apply(lambda g: Point(g.coords[-1]))

    # Add start and end as columns to the gdf
    edges["start_coord"] = first_coord
    edges["end_coord"] = last_coord

    start_coords = edges[["edge_id", "start_coord"]].copy()
    start_coords.set_geometry("start_coord", inplace=True, crs=edges.crs)

    end_coords = edges[["edge_id", "end_coord"]].copy()
    end_coords.set_geometry("end_coord", inplace=True, crs=edges.crs)

    # join start and end coors to nearest node
    start_joined = start_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]],
        how="left",
        distance_col="distance",
        max_distance=max_distance,
    )
    end_joined = end_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]],
        how="left",
        distance_col="distance",
        max_distance=max_distance,
    )
    start_joined = _drop_multiple_joins(start_joined)
    end_joined = _drop_multiple_joins(end_joined)

    assert len(start_joined) == len(edges), "Not all edges have a start node"
    assert len(end_joined) == len(edges), "Not all edges have an end node"

    edges.drop(["start_coord", "end_coord"], axis=1, inplace=True)

    # Merge with edges
    new_edges = edges.merge(
        start_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    new_edges.rename({"node_id": "u"}, inplace=True, axis=1)

    new_edges = new_edges.merge(
        end_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    new_edges.rename({"node_id": "v"}, inplace=True, axis=1)

    assert len(new_edges) == len(
        edges
    ), "New edges geodataframe does not have the same length as the input edges geodataframe"

    return new_edges


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

    edges["key"] = edges["key"].fillna(0)
    edges["key"] = edges["key"].astype(int)

    return edges


def order_edge_nodes(gdf):

    # gdf = gdf[gdf.u.notna() & gdf.v.notna()]

    for index, row in gdf[gdf.u.notna() & gdf.v.notna()].iterrows():
        org_u = row.u
        org_v = row.v

        gdf.loc[index, "u"] = min(org_u, org_v)
        gdf.loc[index, "v"] = max(org_u, org_v)

    return gdf


# define helper function to clean data folders
def remove_output_data(
    output_folders, remove_previous_output: bool = False, verbose: bool = False
):

    if remove_previous_output:
        for f in output_folders:
            if os.path.exists(f):
                shutil.rmtree(f)

                os.makedirs(f)
    if verbose:
        print("Data folder cleaned...")

### TODO previously nw.py

def unzip_line(geom, coordnum = 30):
    longline = [c for c in geom.coords]
    if len(longline)%coordnum == 1:
        coordnum+=1
    linestrings = []
    current_linestring = []
    for c in longline:
        current_linestring.append(c)
        if len(current_linestring) > coordnum:
            linestrings.append(LineString(current_linestring))
            del current_linestring
            current_linestring = [c]
    if current_linestring:
        linestrings.append(LineString(current_linestring))
    return linestrings

def drop_dangling_edges_iter(gdf_network, my_danglefactor, my_buffer, iters=5):
    G = momepy.gdf_to_nx(gdf_network=gdf_network, multigraph = False, integer_labels=True)
    for _ in range(iters):
        degree_one = [n for n in G.nodes if nx.degree(G, n)==1]
        degree_one_to_remove = []
        for n in degree_one:
            if G.edges[list(G.edges(n))[0]]["mm_len"] < my_danglefactor * my_buffer:
                degree_one_to_remove.append(n)
        G.remove_nodes_from(degree_one_to_remove)
    edges = momepy.nx_to_gdf(G, points=False, lines=True)
    edges_rem = momepy.remove_false_nodes(edges)
    edges_rem["i"] = edges_rem.index
    return edges_rem

### TODO: previously raw-to-processed.py

def _drop_multiple_joins(joined_nodes):

    joined_nodes.reset_index(inplace=True)

    v = joined_nodes.edge_id.value_counts()
    grouped = joined_nodes[joined_nodes.edge_id.isin(v.index[v.gt(1)])].groupby(
        "edge_id"
    )

    drop_joined = []
    for edge_id, g in grouped:
        node_id = g.node_id.max()
        drop_joined.append((edge_id, node_id))

    for d in drop_joined:
        joined_nodes.drop(
            joined_nodes[
                (joined_nodes.edge_id == d[0]) & (joined_nodes.node_id == d[1])
            ].index,
            inplace=True,
        )

    return joined_nodes


def assign_edges_start_end_nodes(edges, nodes, max_distance=5):
    """
    Assign node ids of start and end nodes for edges in an edge geodataframe, based on the closest nodes in a node geodataframe

    Arguments:
        edges (gdf): network edges
        nodes (gdf): network nodes

    Returns:
        edges (gdf): edges with u column with start node id and v column with end node id
    """

    # Extract start and end coordinates of each linestring
    first_coord = edges.geometry.apply(lambda g: Point(g.coords[0]))
    last_coord = edges.geometry.apply(lambda g: Point(g.coords[-1]))

    # Add start and end as columns to the gdf
    edges["start_coord"] = first_coord
    edges["end_coord"] = last_coord

    start_coords = edges[["edge_id", "start_coord"]].copy()
    start_coords.set_geometry("start_coord", inplace=True, crs=edges.crs)

    end_coords = edges[["edge_id", "end_coord"]].copy()
    end_coords.set_geometry("end_coord", inplace=True, crs=edges.crs)

    # join start and end coors to nearest node
    start_joined = start_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]],
        how="left",
        distance_col="distance",
        max_distance=max_distance,
    )
    end_joined = end_coords.sjoin_nearest(
        nodes[["geometry", "node_id"]],
        how="left",
        distance_col="distance",
        max_distance=max_distance,
    )
    start_joined = _drop_multiple_joins(start_joined)
    end_joined = _drop_multiple_joins(end_joined)

    assert len(start_joined) == len(edges)
    assert len(end_joined) == len(edges)

    edges.drop(["start_coord", "end_coord"], axis=1, inplace=True)

    # Merge with edges
    new_edges = edges.merge(
        start_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    new_edges.rename({"node_id": "u"}, inplace=True, axis=1)

    new_edges = new_edges.merge(
        end_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
    )
    new_edges.rename({"node_id": "v"}, inplace=True, axis=1)

    assert len(new_edges) == len(edges)

    return new_edges


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

    edges["key"].fillna(0, inplace=True)

    return edges


def order_edge_nodes(gdf):

    # gdf = gdf[gdf.u.notna() & gdf.v.notna()]

    for index, row in gdf[gdf.u.notna() & gdf.v.notna()].iterrows():
        org_u = row.u
        org_v = row.v

        gdf.loc[index, "u"] = min(org_u, org_v)
        gdf.loc[index, "v"] = max(org_u, org_v)

    return gdf


# def _find_parallel_edges(edges):
#     """
#     Check for parallel edges in a pandas DataFrame with edges, including columns u with start node index and v with end node index.
#     If two edges have the same u-v pair, the column 'key' is updated to ensure that the u-v-key combination can uniquely identify an edge.
#     Note that (u,v) is not considered parallel to (v,u)

#     Arguments:
#         edges (gdf): network edges

#     Returns:
#         edges (gdf): edges with updated key index
#     """

#     # Find edges with duplicate node pairs
#     parallel = edges[edges.duplicated(subset=["u", "v"])]

#     edges.loc[parallel.index, "key"] = 1  # Set keys to 1

#     k = 1

#     while len(edges[edges.duplicated(subset=["u", "v", "key"])]) > 0:
#         k += 1

#         parallel = edges[edges.duplicated(subset=["u", "v", "key"])]

#         edges.loc[parallel.index, "key"] = k  # Set keys to 1

#     assert (
#         len(edges[edges.duplicated(subset=["u", "v", "key"])]) == 0
#     ), "Edges not uniquely indexed by u,v,key!"

#     return edges


# def _order_edge_nodes(gdf):

#     for index, row in gdf.iterrows():
#         org_u = row.u
#         org_v = row.v

#         gdf.loc[index, "u"] = min(org_u, org_v)
#         gdf.loc[index, "v"] = max(org_u, org_v)

#     return gdf


# def _assign_edges_start_end_nodes(edges, nodes):
#     """
#     Assign node ids of start and end nodes for edges in an edge geodataframe, based on the closest nodes in a node geodataframe

#     Arguments:
#         edges (gdf): network edges
#         nodes (gdf): network nodes

#     Returns:
#         edges (gdf): edges with u column with start node id and v column with end node id
#     """

#     # Extract start and end coordinates of each linestring
#     first_coord = edges.geometry.apply(lambda g: Point(g.coords[0]))
#     last_coord = edges.geometry.apply(lambda g: Point(g.coords[-1]))

#     # Add start and end as columns to the gdf
#     edges["start_coord"] = first_coord
#     edges["end_coord"] = last_coord

#     start_coords = edges[["edge_id", "start_coord"]].copy()
#     start_coords.set_geometry("start_coord", inplace=True, crs=edges.crs)

#     end_coords = edges[["edge_id", "end_coord"]].copy()
#     end_coords.set_geometry("end_coord", inplace=True, crs=edges.crs)

#     # join start and end coors to nearest node
#     start_joined = start_coords.sjoin_nearest(
#         nodes[["geometry", "node_id"]], how="left", distance_col="distance"
#     )
#     end_joined = end_coords.sjoin_nearest(
#         nodes[["geometry", "node_id"]], how="left", distance_col="distance"
#     )

#     edges.drop(["start_coord", "end_coord"], axis=1, inplace=True)

#     # Merge with edges
#     edges = edges.merge(
#         start_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
#     )
#     edges.rename({"node_id": "u"}, inplace=True, axis=1)

#     edges = edges.merge(
#         end_joined[["edge_id", "node_id"]], left_on="edge_id", right_on="edge_id"
#     )
#     edges.rename({"node_id": "v"}, inplace=True, axis=1)

#     return edges


# #########


# def technical_to_communication(node_gdf, edge_gdf):

#     # copy the gdfs before modifying them
#     edges = edge_gdf.copy()
#     nodes = node_gdf.copy()

#     # create distinct column names for unique id
#     edges["edge_id"] = edges.index
#     assert len(edges) == len(edges.edge_id.unique())
#     nodes["node_id"] = nodes.id
#     assert len(nodes) == len(nodes.node_id.unique())

#     # assign edges initial start and end nodes
#     edges = _assign_edges_start_end_nodes(edges, nodes)

#     # find all child nodes with parents that are not dead ends
#     child_nodes = nodes[(nodes.refmain.notna()) & (nodes.deadend == 0)]

#     edges["modified"] = False

#     # assign edges from child nodes with parents to parent nodes
#     for ix, row in child_nodes.iterrows():
#         idx = ix
#         # ID of this child node
#         this_node_id = row.node_id

#         # geometry of the child nodes parent node
#         parent_geom = nodes.loc[
#             nodes.node_id == int(child_nodes.loc[ix, "refmain"])
#         ].geometry.values[0]
#         # print(f"idx {idx}, step 1")

#         if parent_geom.distance(row.geometry) > 100:
#             continue
#         else:
#             # all edges which have this child node as their start node
#             edges_start = edges.loc[edges.u == this_node_id]

#             # all edges which have this child node as their end node
#             edges_end = edges.loc[edges.v == this_node_id]
#             # print(f"idx {idx}, step 2")

#             for ix, row in edges_start.iterrows():
#                 # get coordinate in edge linestring
#                 edge_coords = list(row.geometry.coords)

#                 # replace start coordinate (child node) with geometry of parent node
#                 edge_coords[0] = parent_geom.coords[0]

#                 # create new linestring from updated coordinates
#                 new_linestring = LineString(edge_coords)

#                 # update edge geometry
#                 edges.loc[ix, "geometry"] = new_linestring

#                 # mark edge as modified
#                 edges.loc[ix, "modified"] = True
#                 # print(f"idx {idx}, step 3")

#             for ix, row in edges_end.iterrows():
#                 # get coordinate in edge linestring
#                 edge_coords = list(row.geometry.coords)

#                 # replace end coordinate (child node) with geometry of parent node
#                 edge_coords[-1] = parent_geom.coords[0]

#                 # create new linestring from updated coordinates
#                 new_linestring = LineString(edge_coords)

#                 # update edge geometry
#                 edges.loc[ix, "geometry"] = new_linestring

#                 # mark edge as modified
#                 edges.loc[ix, "modified"] = True
#                 # print(f"idx {idx}, step 4")

#     # drop old u,v columns
#     edges.drop(["u", "v"], axis=1, inplace=True)

#     # find new start and end nodes
#     edges = _assign_edges_start_end_nodes(edges, nodes)

#     # find edges with same start and end node (but could still be on different roads!)
#     edges["key"] = 0

#     # Set u to be to be the smaller one of u,v nodes (based on node id) - to identify parallel edges between u,v / v,u matches
#     edges = _order_edge_nodes(edges)

#     edges = _find_parallel_edges(edges)

#     # delete modified edges whith same u and v
#     edges.drop(
#         edges.loc[(edges.u == edges.v) & (edges.modified == True)].index, inplace=True
#     )

#     # find parallel edges of approximate same length
#     edges["drop"] = False
#     edges["length"] = edges.geometry.length

#     grouped = edges.groupby(["u", "v"])

#     for name, group in grouped:
#         if len(group) > 1:
#             # compare length of all members in groups pair wise
#             group_lengths = group.length.to_list()

#             duplicates = []
#             # mark as duplicate if length difference is less than 20 %
#             for i in range(len(group_lengths)):
#                 for j in range(i + 1, len(group_lengths)):
#                     if (
#                         abs(
#                             (
#                                 (group_lengths[i] - group_lengths[j])
#                                 / ((group_lengths[i] + group_lengths[j]) / 2)
#                             )
#                             * 100
#                         )
#                         < 8
#                     ):
#                         duplicates.append((group_lengths[i], group_lengths[j]))

#             length_of_edges_to_drop = set([min(d) for d in duplicates])

#             edges.loc[
#                 group.loc[group.length.isin(length_of_edges_to_drop)].index, "drop"
#             ] = True

#     # nodes used by new network edges
#     nodes_in_use = nodes.loc[
#         nodes.node_id.isin(set(edges.u.to_list() + edges.v.to_list()))
#     ]

#     # edges without parallel edges
#     edges_no_parallel = edges.loc[edges["drop"] == False]

#     assert len(edges) == len(edges.edge_id.unique())
#     assert len(edges_no_parallel) == len(edges_no_parallel.edge_id.unique())
#     assert len(nodes_in_use) == len(nodes_in_use.id.unique())

#     return nodes_in_use, edges_no_parallel, edges

def load_evaluation_data(homepath):
    # load evaluation data
    evaldict = {}

    for geomtype in [
        "point",
        # "linestring",
        "polygon",
    ]:
        geompath_input = homepath + f"/data/input/{geomtype}/"
        geompath_output = homepath + f"/data/output/{geomtype}/"
        
        if os.path.exists(geompath_input):

            geomlayers = os.listdir(geompath_input)
            geomlayers = [g for g in geomlayers if not ("gpkg-wal" in g or "gpkg-shm" in g or ".md" in g)]
            evaldict[geomtype] = {}

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
    return evaldict