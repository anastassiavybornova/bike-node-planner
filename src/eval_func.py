# import libraries
import os

os.environ["USE_PYGEOS"] = "0"  # pygeos/shapely2.0/osmnx conflict solving
import geopandas as gpd
import pandas as pd
from shapely import strtree

def merge_municipalities(
        municipality_codes, 
        evaluation_layer, 
        input_folder, 
        output_folder        
        ):
    """
    For a given evaluation layer, merges data of all given municipalities and saves output to file.

    Arguments:
        municipality_codes (list of str): list of 4-digit municipality codes (str format)
        evaluation_layer (str): name of evaluation layer, has to be one of: "agriculture", "bad", "culture", "facilities", "nature", "pois", "service"
        input_folder (str): path to folder where subfolders with municipality data are located
        output_folder (str): path to folder where merged gdf will be saved to
    
    Returns:
        None
    """
    gdfs = []
    for m in municipality_codes:
        layerpath = input_folder + f"municipality_data/{m}/{evaluation_layer}.gpkg"
        if os.path.exists(layerpath):
            gdfs.append(gpd.read_file(layerpath))
    if len(gdfs) > 1:
        gdfs = pd.concat(gdfs, join = "inner", ignore_index = True)
        gdfs.to_file(output_folder + f"{evaluation_layer}.gpkg")
        print(f"{evaluation_layer.capitalize()} layer created")
    elif len(gdfs) == 1:
        gdfs[0].to_file(output_folder + f"{evaluation_layer}.gpkg")
        print(f"{evaluation_layer.capitalize()} layer created")
    else:
        print(f"No {evaluation_layer} data found for this study area")
    return None

def evaluate_export_plot_point(
    input_fp,
    within_reach_output_fp,
    outside_reach_output_fp,
    network_edges,
    dist,
    name,
    type_col,
    input_color_rgb="255, 0, 0",
    output_color_reached="255, 0, 0",
    output_color_not_reached="255, 0, 0",
    input_size=3,
    output_size_reached=3,
    output_size_not_reached=3,
    input_alpha="255",
    output_alpha="255",
    display_output=True,
    display_input=True,
):
    """
    Find points reachable from network edges, export reachable and unreachable points and plot results

    Arguments:
        input_fp (str): filepath for input points
        within_reach_output_fp (str): filepath for storing points within reach
        outside_reach_output_fp (str): filepath for storing points outside reach
        network_edges (gdf): network edges as GeoDataFrame
        dist (numeric): max distance for points to be reachable (in meters)
        name (str): label/name for points layer (used for layer naming and print statements)
        type_col (str): name of column with sub-category for points
        input_color_rgb (str): String with 3 rgb values for input color
        input_size (numerical): marker size when plotting input points
        output_size_reached (numerical): marker size when plotting reachable points
        output_size_not_reached (numerical): marker size when plotting non-reachable points
        input_alpha (numerical): value between 0 and 255 setting the transparency of input points
        output_alpha (numerical): value between 0 and 255 setting the transparency of reachable and non-reachable points
        display_output (bool): If True, plots reachable and non reachable points
        display_input (bool): If True, plots input points

    Returns:
        input_layer_name (str), output_layer_name_within (str), output_layer_name_outside (str):
        Returns names of plotted layers with input, non-reachable points and reachable points
        If the display of a layer is set to False, None is returned instead of the layer name
        res (dict): summary statistics of evaluation results
    """

    # import layer
    input_points = gpd.read_file(input_fp)

    # evaluate
    evaluated_points = evaluate_point_layer(input_points, network_edges, dist)
    print(f"{name} layer evaluated")

    points_withinreach = evaluated_points.loc[evaluated_points.withinreach == 1]
    print(
        f"Out of {len(input_points)} {name.lower()} points, {len(points_withinreach)} {name.lower()} ({(len(points_withinreach) / len(input_points))*100:.2f}%) are within reach"
    )
    
    # export
    points_withinreach.to_file(within_reach_output_fp)

    evaluated_points.loc[evaluated_points.withinreach == 0].to_file(
        outside_reach_output_fp
    )
    
    # stats to dict
    res = {}
    res[name] = {}
    res[name]["type"] = "point_layer"
    res[name]["dist"] = dist
    res[name]["total"] = len(input_points)
    res[name]["within"] = len(points_withinreach)
    res[name]["outside"] = len(evaluated_points.loc[evaluated_points.withinreach == 0])

    input_layer_name = None
    output_layer_name_within = None
    output_layer_name_outside = None

    # plot
    if display_input:
        input_layer_name = name

        vlayer_input = QgsVectorLayer(input_fp, input_layer_name, "ogr")

        QgsProject.instance().addMapLayer(vlayer_input)

        draw_simple_point_layer(
            input_layer_name,
            color=input_color_rgb + "," + input_alpha,
            marker_size=input_size,
            outline_width=0,
        )

    if display_output:
        output_layer_name_outside = f"{name} outside reach"

        vlayer_outside = QgsVectorLayer(
            outside_reach_output_fp, output_layer_name_outside, "ogr"
        )

        QgsProject.instance().addMapLayer(vlayer_outside)
        draw_categorical_layer(
            output_layer_name_outside,
            type_col,
            predefined_color = output_color_not_reached,
            alpha=output_alpha,
            marker_size=output_size_not_reached,
        )

        output_layer_name_within = f"{name} within reach"
        vlayer_within = QgsVectorLayer(
            within_reach_output_fp, output_layer_name_within, "ogr"
        )

        QgsProject.instance().addMapLayer(vlayer_within)
        draw_categorical_layer(
            output_layer_name_within,
            type_col,
            predefined_color = output_color_reached,
            alpha=output_alpha,
            marker_size=output_size_reached,
        )

    return input_layer_name, output_layer_name_within, output_layer_name_outside, res

def evaluate_export_plot_poly(
    input_fp,
    output_fp,
    network_edges,
    dist,
    name,
    type_col,
    fill_color_rgb,
    outline_color_rgb,
    line_color_rgb,
    line_width=1,
    line_style="solid",
    plot_categorical=False,
    fill_alpha="100",
    outline_alpha="200",
    display_output=True,
    display_input=True,
):
    """
    Find intersection between network edges and polygon layer, export intersection and plot outcome

    Arguments:
        input_fp (str): Filepath to polygon layer
        output_fp (str): Filepath for storing intersecting edges
        network_edges (gdf): Network edges
        dist (numeric): Distance to use for buffering polygons
        name (str): Name of polygon layer (used for layer naming and print statements)
        type_col (str): Name of column in polygon layer with sub-category/type
        fill_color_rgb (str): String with RGB values for the fill color used for plotting the input polygons
        outline_color_rgb (str): String with RGB values for the outline color used for plotting the input polygons
        line_color_rgb (str):  String with RGB values for the color used for plotting intersecting network
        line_width (numerical): Line width when plotting the intersecting network
        line_style (str): Plot style for plotting intersecting network (e.g. "solid" or "dash")
        plot_categorical (bool): If True, plots the intersecting edges using a categorical plotting based on the type of intersecting polygon
        fill_alpha (str): String with value between 0 and 255 setting the transparency of the polygon fill
        outline_alpha (str): String with value between 0 and 255 setting the transparency of the polygon outline
        display_output (bool): If True, plot the intersecting network edges
        display_input (bool): If True, plot the input polygons
    Returns:
        input_layer_name (str), output_layer_name (str):
        Returns names of plotted layers with input and output (intersecting edges)
        If the display of a layer is set to False, None is returned instead of the layer name
    """
    # import layer
    input_poly = gpd.read_file(input_fp)

    # evaluate
    evaluate_network, evaluate_area = evaluate_polygon_layer(input_poly, network_edges, dist)

    print(f"{name} areas evaluated")
    print(
        f"{evaluate_network.unary_union.length / 1000:.2f} out of {network_edges.unary_union.length / 1000:.2f} km ({(evaluate_network.unary_union.length / network_edges.unary_union.length)*100:.2f}%) of the network go through {name.lower()} areas."
    )

    # export
    evaluate_network.to_file(output_fp)

    # stats to dict
    res = {}
    res[name] = {}
    res[name]["type"] = "polygon_layer"
    res[name]["dist"] = dist
    res[name]["total"] = network_edges.unary_union.length # area covered by layer
    res[name]["within"] = evaluate_network.unary_union.length # length of edges intersecting
    res[name]["outside"] = network_edges.unary_union.length - evaluate_network.unary_union.length # length of edges not intersecting 
    res[name]["area"] = evaluate_area

    input_layer_name = None
    output_layer_name = None

    # plot
    if display_input:
        input_layer_name = f"{name} areas"

        vlayer_in = QgsVectorLayer(input_fp, input_layer_name, "ogr")

        QgsProject.instance().addMapLayer(vlayer_in)
        draw_simple_polygon_layer(
            input_layer_name,
            color=fill_color_rgb + "," + fill_alpha,
            outline_color=outline_color_rgb + "," + outline_alpha,
            outline_width=0.5,
        )

    if display_output:
        output_layer_name = f"Network in {name.lower()} areas"

        vlayer_out = QgsVectorLayer(output_fp, output_layer_name, "ogr")
        QgsProject.instance().addMapLayer(vlayer_out)

        if plot_categorical:
            draw_categorical_layer(output_layer_name, type_col)

        else:
            draw_simple_line_layer(
                output_layer_name,
                line_color_rgb,
                line_width=line_width,
                line_style=line_style,
            )

    return input_layer_name, output_layer_name, res


def evaluate_polygon_layer(poly, edges, polygon_buffer=100):
    """
    find out where study_area linestrings intersect with a given
    polygon layer. linestrings are buffered with a default of 100m.
    both input gdfs must be in the same projected CRS.
    keep track of which, and how many, types (from poly layer)
    each of the edge segments intersects with (to track variation).
    returns 
        gdf of intersecting edge segments
        surface (sqm) of evaluation area
    """

    assert poly.crs == edges.crs

    # explode edges
    edges = edges.explode(index_parts=False)

    # buffer polygons
    poly["geometry"] = poly.buffer(polygon_buffer)
    poly_area = poly.unary_union

    # strtree query to find which edge intersects with which type of polygon
    # (to check for variation)

    # make strtree of edge geoms
    mytree = strtree.STRtree(geoms=poly.geometry)
    type_inter = []  # list to add as column after for-loop

    # for each polygon,
    for ix, row in edges.iterrows():
        # find intersection of polygon with edges
        q = mytree.query(row.geometry, predicate="intersects")
        # combining all unique (cf set()), sorted types in a string (so hashable)
        types = ""
        for t in sorted(list(set(poly.loc[q, "type"]))):
            types += t + "_"  # adding _ after each type (to count)
        type_inter.append(types)  # append to list of sets

    edges["type_inter"] = type_inter
    edges["type_count"] = edges.apply(lambda x: x.type_inter.count("_"), axis=1)

    # we already know with what "type" of polygon they intersect;
    # now we find the geometries of the intersections:
    geoms_inter = edges.intersection(poly_area)
    gdf_inter = gpd.GeoDataFrame(
        {
            "geometry": geoms_inter,
            "types": edges["type_inter"],
            "types_count": edges["type_count"],
        },
        crs=edges.crs,
    )

    # explode multilinestrings
    gdf_inter = gdf_inter.explode(index_parts=False)
    # remove empty geoms
    gdf_inter = gdf_inter[-gdf_inter.is_empty].reset_index(drop=True)
    # remove non-linestring geoms
    gdf_inter = gdf_inter[gdf_inter.type == "LineString"].reset_index(drop=True)

    return gdf_inter, poly_area.area


def evaluate_point_layer(points, edges, points_buffer):
    """
    find out where buffered study_area linestrings intersect with a given
    point layer. both input gdfs must be in the same projected CRS.
    keep track of which, and how many, types (from poly layer)
    each of the edge segments intersects with (to track variation).
    """

    assert points.crs == edges.crs

    # explode points
    points = points.explode(index_parts=False)

    # explode edges
    edges = edges.explode(index_parts=False)

    # buffer edges
    edges_buff = edges.copy()
    edges_buff["geometry"] = edges_buff.buffer(points_buffer)
    edges_buff_area = edges_buff.unary_union

    # return gdf of points with info whether they are within reach or not
    points["withinreach"] = 0
    # make strtree of edge geoms
    mytree = strtree.STRtree(geoms=points.geometry)
    q = mytree.query(edges_buff_area, predicate="intersects")
    # the ones that intersect with the buffered edge area, are within reach
    points.loc[q, "withinreach"] = 1

    # not included, but maybe later? also return edges with info WHICH point is within reach
    # (again, accounting for variation)

    return points