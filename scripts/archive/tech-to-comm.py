import numpy as np
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import shapely
from shapely.ops import linemerge
from shapely.geometry import LineString, Point


def _find_parallel_edges(edges):
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


def _order_edge_nodes(gdf):

    for index, row in gdf.iterrows():
        org_u = row.u
        org_v = row.v

        gdf.loc[index, "u"] = min(org_u, org_v)
        gdf.loc[index, "v"] = max(org_u, org_v)

    return gdf

def _assign_edges_start_end_nodes(edges, nodes):
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

#########

def technical_to_communication(node_gdf, edge_gdf):

    # copy the gdfs before modifying them
    edges = edge_gdf.copy()
    nodes = node_gdf.copy()

    # create distinct column names for unique id
    edges["edge_id"] = edges.index
    assert len(edges) == len(edges.edge_id.unique())
    nodes["node_id"] = nodes.id
    assert len(nodes) == len(nodes.node_id.unique())

    # assign edges initial start and end nodes
    edges = _assign_edges_start_end_nodes(edges, nodes)

    # find all child nodes with parents that are not dead ends
    child_nodes = nodes[(nodes.refmain.notna()) & (nodes.deadend == 0)]

    edges["modified"] = False

    # assign edges from child nodes with parents to parent nodes
    for ix, row in child_nodes.iterrows():
        idx = ix
        # ID of this child node
        this_node_id = row.node_id

        # geometry of the child nodes parent node
        parent_geom = nodes.loc[
            nodes.node_id == int(child_nodes.loc[ix, "refmain"])
        ].geometry.values[0]
        # print(f"idx {idx}, step 1")

        if parent_geom.distance(row.geometry) > 100:
            continue
        else:
            # all edges which have this child node as their start node
            edges_start = edges.loc[edges.u == this_node_id]

            # all edges which have this child node as their end node
            edges_end = edges.loc[edges.v == this_node_id]
            # print(f"idx {idx}, step 2")

            for ix, row in edges_start.iterrows():
                # get coordinate in edge linestring
                edge_coords = list(row.geometry.coords)

                # replace start coordinate (child node) with geometry of parent node
                edge_coords[0] = parent_geom.coords[0]

                # create new linestring from updated coordinates
                new_linestring = LineString(edge_coords)

                # update edge geometry
                edges.loc[ix, "geometry"] = new_linestring

                # mark edge as modified
                edges.loc[ix, "modified"] = True
                # print(f"idx {idx}, step 3")

            for ix, row in edges_end.iterrows():
                # get coordinate in edge linestring
                edge_coords = list(row.geometry.coords)

                # replace end coordinate (child node) with geometry of parent node
                edge_coords[-1] = parent_geom.coords[0]

                # create new linestring from updated coordinates
                new_linestring = LineString(edge_coords)

                # update edge geometry
                edges.loc[ix, "geometry"] = new_linestring

                # mark edge as modified
                edges.loc[ix, "modified"] = True
                # print(f"idx {idx}, step 4")

    # drop old u,v columns
    edges.drop(["u", "v"], axis=1, inplace=True)

    # find new start and end nodes
    edges = _assign_edges_start_end_nodes(edges, nodes)

    # find edges with same start and end node (but could still be on different roads!)
    edges["key"] = 0

    # Set u to be to be the smaller one of u,v nodes (based on node id) - to identify parallel edges between u,v / v,u matches
    edges = _order_edge_nodes(edges)

    edges = _find_parallel_edges(edges)

    # delete modified edges whith same u and v
    edges.drop(
        edges.loc[(edges.u == edges.v) & (edges.modified == True)].index, inplace=True
    )

    # find parallel edges of approximate same length
    edges["drop"] = False
    edges["length"] = edges.geometry.length

    grouped = edges.groupby(["u", "v"])

    for name, group in grouped:
        if len(group) > 1:
            # compare length of all members in groups pair wise
            group_lengths = group.length.to_list()

            duplicates = []
            # mark as duplicate if length difference is less than 20 %
            for i in range(len(group_lengths)):
                for j in range(i + 1, len(group_lengths)):
                    if (
                        abs(
                            (
                                (group_lengths[i] - group_lengths[j])
                                / ((group_lengths[i] + group_lengths[j]) / 2)
                            )
                            * 100
                        )
                        < 8
                    ):
                        duplicates.append((group_lengths[i], group_lengths[j]))

            length_of_edges_to_drop = set([min(d) for d in duplicates])

            edges.loc[
                group.loc[group.length.isin(length_of_edges_to_drop)].index, "drop"
            ] = True

    # nodes used by new network edges
    nodes_in_use = nodes.loc[nodes.node_id.isin(set(edges.u.to_list() + edges.v.to_list()))]

    # edges without parallel edges
    edges_no_parallel = edges.loc[edges["drop"] == False]

    assert len(edges) == len(edges.edge_id.unique())
    assert len(edges_no_parallel) == len(edges_no_parallel.edge_id.unique())
    assert len(nodes_in_use) == len(nodes_in_use.id.unique())
    
    return nodes_in_use, edges_no_parallel, edges