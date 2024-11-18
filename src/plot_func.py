import os
import re
import yaml
import random
from random import randrange

import numpy as np
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import contextily as cx
import seaborn as sns

random.seed(42)
# from qgis.core import QgsVectorLayer
from qgis.core import *
from qgis.utils import iface

from ast import literal_eval

edge_classification_colors = {
    "too_short": "#000000",
    "ideal_range": "#00CB00",
    "above_ideal": "#FFB900",
    "too_long": "#E10000",
}

loop_classification_colors = {
    "too_short": "0,0,0,128",
    "ideal_range": "0,203,0,128",
    "too_long": "225,0,0,128",
}


def rgb2hex(rgb_string):
    return "#%02x%02x%02x" % tuple([int(n) for n in rgb_string.split(",")])[0:3]


def rgb_shade(rgb_string, shade=0.6):
    # return rgb string shaded (darkened) by a factor of *shade*
    rbg_shaded = [int(shade * v) for v in literal_eval(rgb_string)]
    rgb_shaded_string = str(rbg_shaded).replace("[", "").replace("]", "")
    return rgb_shaded_string


def move_group(group_name, position=0):
    root = QgsProject.instance().layerTreeRoot()

    group = root.findGroup(group_name)
    group_clone = group.clone()
    root.insertChildNode(position, group_clone)
    root.removeChildNode(group)


def move_basemap_back(basemap_name="Basemap"):
    # get basemap layer
    layer = QgsProject.instance().mapLayersByName(basemap_name)[0]

    # clone
    cloned_layer = layer.clone()

    # add clone to instance, but not map/TOC
    QgsProject.instance().addMapLayer(cloned_layer, False)

    root = QgsProject.instance().layerTreeRoot()

    # insert at bottom of TOC
    root.insertLayer(-1, cloned_layer)

    # remove original
    root.removeLayer(layer)


def turn_off_layers(layer_names):
    for l in layer_names:
        layer = QgsProject.instance().mapLayersByName(l)[0]

        QgsProject.instance().layerTreeRoot().findLayer(
            layer.id()
        ).setItemVisibilityChecked(False)


def turn_on_layers(layer_names):
    for l in layer_names:
        layer = QgsProject.instance().mapLayersByName(l)[0]

        QgsProject.instance().layerTreeRoot().findLayer(
            layer.id()
        ).setItemVisibilityChecked(True)


def add_layer_to_group(layer_name, group, position=-1):
    """
    Add layer to existing layer group

    Arguments:
        layer_name (str): name of layer to plot
        group (QgsLayerTreeGroup): Group to add layer to
        position (int): Position of layer. Set to -1 to add as bottom layer and 0 to add as top layer
    Returns:
        None
    """
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    tree_layer = root.findLayer(layer.id())
    cloned_layer = tree_layer.clone()
    parent = tree_layer.parent()

    group.insertChildNode(position, cloned_layer)

    parent.removeChildNode(tree_layer)


def group_layers(group_name, layer_names, remove_group_if_exists=True):
    """
    Create new group and add layers to it.
    group_name ... name of the new group.
    layer_names ... names of (already existing in the project) layers to add.
    """
    root = QgsProject.instance().layerTreeRoot()

    # remove group AND included layers if group already exists
    if remove_group_if_exists:
        for group in [child for child in root.children() if child.nodeType() == 0]:
            if group.name() == group_name:
                root.removeChildNode(group)

    # create new group
    layer_group = root.addGroup(group_name)

    # add layers to new group by first cloning, adding clone, removing original parent
    for layer_name in layer_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

        tree_layer = root.findLayer(layer.id())
        if tree_layer:
            cloned_layer = tree_layer.clone()
            parent = tree_layer.parent()

            layer_group.insertChildNode(0, cloned_layer)

            parent.removeChildNode(tree_layer)


def color_ramp_items(colormap, nclass):
    """
    Returns nclass colors from color map
    """
    # https://gis.stackexchange.com/questions/118775/assigning-color-ramp-using-pyqgis
    fractional_steps = [i / nclass for i in range(nclass + 1)]
    ramp = QgsStyle().defaultStyle().colorRamp(colormap)
    colors = [ramp.color(f) for f in fractional_steps]

    return colors


def change_alpha(q_color, alpha):
    color_string_list = str(q_color).split()

    rgb_values = color_string_list[2:-1]

    rgb_values.append(str(alpha))

    rgb_string = " ".join(rgb_values)

    return rgb_string


def draw_linear_graduated_layer(
    layer_name,
    attr_name,
    no_classes,
    cmap="Viridis",
    outline_color="black",
    outline_width=0.5,
    alpha=180,
    line_width=1,
    line_style="solid",
    marker_shape="circle",
    marker_size=2,
    marker_angle=45,
):
    """
    Plot graduated vector later using an equal interval/linearly interpolated color ramp

    Arguments:
        layer_name (str): name of layer to plot
        attr_name (str): name of attr/field used for the classification
        no_classes (int): number of classes
        cmap (str): name of color map
        outline_color (str): color to use for outline color for points and polygons
        outline_width (numerical): width of outline for points and polygons
        alpha (numerical): value between 0 and 255 setting the transparency of the fill color
        linewidth (numerical): width of line features
        line_style (string): line style (e.g. solid or dash). Must be valid line style type
        marker_shape (string): shape of marker for point features. Must be valid shape name
        marker_size (numerical): size of marker for point features
        marker_angle (numerical): value between 0 and 360 indicating the angle of marker for point objects
    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    idx = layer.fields().indexOf(attr_name)

    unique_values = layer.uniqueValues(idx)

    min_val = min(unique_values)
    max_val = max(unique_values)

    value_range = float(max_val) - float(min_val)

    step = value_range / no_classes

    bins = []

    val = float(min_val)

    for i in range(no_classes):
        bins.append(val)
        val += step

    bins.append(float(max_val))

    colors = color_ramp_items(cmap, no_classes)

    classes = []
    for i in range(len(bins) - 1):
        c = (bins[i], bins[i + 1], colors[i])
        classes.append(c)

    ranges = []

    properties = {}

    for i, c in enumerate(classes):
        if layer.wkbType() in [QgsWkbTypes.MultiPolygon, QgsWkbTypes.Polygon]:
            properties = {
                "color": change_alpha(c[2], alpha),
                "outline_color": outline_color,
                "outline_width": outline_width,
            }

            symbol = QgsFillSymbol.createSimple(properties)

        if layer.wkbType() in [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString]:
            symbol = QgsLineSymbol.createSimple(
                {
                    "color": change_alpha(c[2], alpha),
                    "width": line_width,
                    "line_style": line_style,
                }
            )
        if layer.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint]:
            symbol = QgsMarkerSymbol.createSimple(properties)

            properties = {
                "name": marker_shape,
                "size": marker_size,
                "color": change_alpha(c[2], alpha),
                "outline_color": outline_color,
                "outline_width": outline_width,
                "angle": marker_angle,
            }

        render_range = QgsRendererRange(
            QgsClassificationRange(
                f"{c[0]}-{c[1]}",
                c[0],
                c[1],
            ),
            symbol,
        )

        ranges.append(render_range)

    renderer = QgsGraduatedSymbolRenderer(attr_name, ranges)

    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def zoom_to_layer(layer_name):
    """
    Zoom to layer extent

    Arguments:
        input_layer (str): name of vector layer to zoom to

    Returns:
        None
    """
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    # iface.setActiveLayer(my_layer)
    # layer = iface.activeLayer()

    canvas = iface.mapCanvas()
    extent = layer.extent()
    canvas.setExtent(extent)
    canvas.refresh()


def draw_categorical_layer(
    layer_name,
    attr_name,
    predefined_color=None,
    outline_color="black",
    outline_width=0.2,
    alpha=180,
    line_width=1,
    line_style="solid",
    marker_shape="circle",
    marker_size=4,
    marker_angle=45,
):
    # based on https://gis.stackexchange.com/questions/175068/applying-categorized-symbol-to-each-feature-using-pyqgis
    """
    Plot layer based on categorical values with random colors

    Arguments:
        layer_name (str): name of layer to plot
        attr_name (str): name of attribute with categorical values
        predefined_color (str or None): if None, random colors will be generated for each item;
            if str, has to be string of three values between 0 and 255 (RGB)
        outline_color (str): color to use for outline color for points and polygons
        outline_width (numerical): width of outline for points and polygons
        alpha (numerical): value between 0 and 255 setting the transparency of the fill color
        line_width (numerical): width of line features
        line_style (string): line style (e.g. solid or dash). Must be valid line style type
        marker_shape (string): shape of marker for point features. Must be valid shape name
        marker_size (numerical): size of marker for point features
        marker_angle (numerical): value between 0 and 360 indicating the angle of marker for point objects

    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    idx = layer.fields().indexOf(attr_name)

    unique_values = layer.uniqueValues(idx)

    properties = {}

    categories = []

    for unique_value in unique_values:
        if not predefined_color:
            current_color = f"{randrange(0, 256)}, {randrange(0, 256)}, {randrange(0, 256)}, {alpha}"
        else:
            current_color = f"{predefined_color}, {alpha}"

        if layer.wkbType() in [QgsWkbTypes.MultiPolygon, QgsWkbTypes.Polygon]:
            properties = {
                "color": current_color,
                "outline_color": outline_color,
                "outline_width": outline_width,
            }

            symbol = QgsFillSymbol.createSimple(properties)

        if layer.wkbType() in [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString]:
            symbol = QgsLineSymbol.createSimple(
                {
                    "color": current_color,
                    "width": line_width,
                    "line_style": line_style,
                }
            )

        if layer.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint]:
            properties = {
                "name": marker_shape,
                "size": marker_size,
                "color": current_color,
                "outline_color": outline_color,
                "outline_width": outline_width,
                "angle": marker_angle,
            }

            symbol = QgsMarkerSymbol.createSimple(properties)

        # create renderer object
        category = QgsRendererCategory(unique_value, symbol, str(unique_value))

        # entry for the list of category items
        categories.append(category)

    # create renderer object
    renderer = QgsCategorizedSymbolRenderer(attr_name, categories)
    layer.setRenderer(renderer)

    layer.triggerRepaint()  # if the layer was already loaded
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def draw_simple_polygon_layer(
    layer_name, color="0,0,0,128", outline_color="black", outline_width=1
):
    """
    Plot simple polygon layer

    Arguments:
        layer_name (str): name of layer to plot
        color (str): color for polygon fill. If passed as an RGB tuple, fourth value sets the transparency (0-255)
        outline_color (str): color to use for outline color for points and polygons

    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    # iface.setActiveLayer(my_layer)
    # layer = iface.activeLayer()

    properties = {
        "color": color,
        "outline_color": outline_color,
        "outline_width": outline_width,
    }

    symbol = QgsFillSymbol.createSimple(properties)

    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()  # if the layer was already loaded
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def draw_simple_line_layer(
    layer_name, color="purple", line_width=1, line_style="solid"
):
    """
    Plot simple line layer

    Arguments:
        layer_name (str): name of layer to plot
        color (str): color for polygon fill. If passed as an RGB tuple, fourth value sets the transparency (0-255)
        linewidth (numerical): width of line features
        line_style (string): line style (e.g. solid or dash). Must be valid line style type

    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    properties = {"color": color, "width": line_width, "line_style": line_style}

    symbol = QgsLineSymbol.createSimple(properties)

    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def draw_simple_point_layer(
    layer_name,
    color="0,0,0,255",
    marker_shape="circle",
    marker_size=4,
    outline_color="black",
    outline_width=1,
    marker_angle=45,
):
    """
    Plot simple point layer

    Arguments:
        layer_name (str): name of layer to plot
        color (str): color for polygon fill. If passed as an RGB tuple, fourth value sets the transparency (0-255)
        marker_shape (string): shape of marker for point features. Must be valid shape name
        marker_size (numerical): size of marker for point features
        outline_color (str): color to use for outline color for points and polygons
        outline_width (numerical): width of outline for points and polygons
        marker_angle (numerical): value between 0 and 360 indicating the angle of marker for point objects

    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    properties = {
        "name": marker_shape,
        "size": marker_size,
        "color": color,
        "outline_color": outline_color,
        "outline_width": outline_width,
        "angle": marker_angle,
    }
    symbol = QgsMarkerSymbol.createSimple(properties)
    renderer = QgsSingleSymbolRenderer(symbol)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def draw_recent_simple_line_layer(color="purple", width=0.7, line_style="solid"):
    symbol = QgsLineSymbol.createSimple(
        {"color": color, "width": width, "line_style": line_style}
    )
    renderer = QgsSingleSymbolRenderer(symbol)
    iface.activeLayer().setRenderer(renderer)
    iface.activeLayer().triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(iface.activeLayer().id())


def remove_existing_layers(nameparts):
    nameparts = [n.replace(" ", "_") for n in nameparts]
    existing_layers = [
        layer.id() for layer in QgsProject.instance().mapLayers().values()
    ]
    layers_to_remove = [l for l in existing_layers if any([e in l for e in nameparts])]
    for r in layers_to_remove:
        QgsProject.instance().removeMapLayer(r)
    return None


def draw_slope_layer(
    layer_name,
    slope_ranges,
    slope_colors,
    slope_field="slope",
    line_width=1,
    line_style="solid",
):
    """
    Plot network slope layer with a graduated classification based on predefined classes.

    Arguments:
        layer_name (str): name of layer to plot,
        slope_ranges (list): List of tuples with each four values: (label for class (str), lower bound for slope class (numeric), uppper bound for slope class (numeric), color (str))
        slope_field (str): name of attr/field with slope values
        linewidth (numerical): width of line features
        line_style (string): line style (e.g. solid or dash). Must be valid line style type
    Returns:
        None
    """

    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    ranges = []

    slope_ranges += [100]  # add max value (upper limit)
    # make pairs of upper-lower limits for ranges
    slope_pairs = [list(pair) for pair in zip(slope_ranges, slope_ranges[1:])]

    slope_names = [
        f"{slope_pairs[0][0]}-{slope_pairs[0][1]}% (manageable elevation)",
        f"{slope_pairs[1][0]}-{slope_pairs[1][1]}% (noticeable elevation)",
        f"{slope_pairs[2][0]}-{slope_pairs[2][1]}% (steep elevation)",
        f">{slope_pairs[3][0]}% (very steep elevation)",
    ]

    # to make sure upper and lower limit are not identical for disparate ranges:
    for i in range(len(slope_pairs) - 1):
        slope_pairs[i][1] -= 10**-6
    slope_defs = [z for z in zip(slope_names, slope_pairs, slope_colors)]

    for label, (lower, upper), color in slope_defs:
        symbol = QgsLineSymbol.createSimple(
            {
                "width": line_width,
                "line_style": line_style,
            }
        )
        # sym = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(QColor(color))
        rng = QgsRendererRange(lower, upper, symbol, label)
        ranges.append(rng)

    renderer = QgsGraduatedSymbolRenderer(slope_field, ranges)

    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())


def plot_edge_lengths(homepath, edge_classification_colors):

    topo_folder = homepath + "/data/output/network/topology/"

    config = yaml.load(
        open(homepath + "/config/config-topological-analysis.yml"),
        Loader=yaml.FullLoader,
    )
    [ideal_length_lower, ideal_length_upper] = config["ideal_length_range"]
    max_length = config["max_length"]

    edge_classification_labels = {
        "too_short": f"(<{ideal_length_lower}km)",
        "ideal_range": f"({ideal_length_lower}-{ideal_length_upper}km)",
        "above_ideal": f"({ideal_length_upper}-{max_length}km)",
        "too_long": f"(>{max_length}km)",
    }

    gdf = gpd.read_file(topo_folder + "edges_length_classification.gpkg")

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    for classification in gdf.length_class.unique():
        gdf[gdf.length_class == classification].plot(
            ax=ax,
            color=edge_classification_colors[classification],
            label=classification.replace("_", " ")
            + " "
            + edge_classification_labels[classification],
        )
    ax.legend()
    ax.set_title("Edge length evaluation")
    ax.set_axis_off()
    fig.savefig(
        homepath + f"/results/plots/edgelengths.png", dpi=300, bbox_inches="tight"
    )
    plt.close()

    return None


def plot_loop_lengths(homepath, loop_classification_colors):

    topo_folder = homepath + "/data/output/network/topology/"

    config = yaml.load(
        open(homepath + "/config/config-topological-analysis.yml"),
        Loader=yaml.FullLoader,
    )

    [loop_length_min, loop_length_max] = config["loop_length_range"]

    loop_classification_labels = {
        "too_short": f"(<{loop_length_min}km)",
        "ideal_range": f"({loop_length_min}-{loop_length_max}km)",
        "too_long": f"(>{loop_length_max}km)",
    }

    gdf = gpd.read_file(topo_folder + "loops_length_classification.gpkg")

    gdf["color_plot"] = gdf.length_class.apply(
        lambda x: rgb2hex(loop_classification_colors[x])
    )

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    gdf.plot(ax=ax, color=gdf.color_plot, alpha=0.5)
    gdf.plot(ax=ax, facecolor="none", edgecolor="black", linestyle="dashed")
    ax.set_title("Loop length evaluation")
    ax.set_axis_off()
    # add custom legend
    custom_lines = [
        Line2D([0], [0], color=rgb2hex(k), lw=4, alpha=0.5)
        for k in loop_classification_colors.values()
    ]
    ax.legend(custom_lines, loop_classification_labels.values())
    fig.savefig(
        homepath + f"/results/plots/looplengths.png", dpi=300, bbox_inches="tight"
    )
    plt.close()

    return None


def render_heatmap(
    layer, layer_name, radius=10, weight_field=None, color_ramp="Spectral"
):

    # layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    clone = layer.clone()
    clone.setName(layer_name + " heatmap")
    QgsProject.instance().addMapLayer(clone)

    renderer = QgsHeatmapRenderer()
    renderer.setRadius(radius)
    renderer.setWeightExpression(weight_field)
    clone.setRenderer(renderer)

    col_ramp = QgsStyle().defaultStyle().colorRamp(color_ramp)
    col_ramp.invert()
    col_ramp.setColor1(QColor(43, 131, 186, 0))
    renderer.setColorRamp(col_ramp)

    clone.triggerRepaint()


def remove_layout(layout_name):
    project = QgsProject.instance()
    manager = project.layoutManager()
    layouts_list = manager.printLayouts()

    for layout in layouts_list:
        if layout.name() == layout_name:
            manager.removeLayout(layout)


def find_largest_bbox(layers):
    bbox = None
    for layer in layers:
        if bbox is None:
            bbox = layer.extent()
        else:
            bbox.combineExtentWith(layer.extent())
    return bbox


### PLOTTING FUNCTIONS FOR SUMMARY RESULTS (SCRIPT07)


def plot_study_area(study_area, network_edges, homepath):

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # plot study area
    study_area.plot(ax=ax, color=rgb2hex("250,181,127"), alpha=0.5, zorder=1)
    # plot network
    network_edges.plot(ax=ax, color="black", linewidth=1)
    cx.add_basemap(ax=ax, source=cx.providers.CartoDB.Voyager, crs=study_area.crs)

    ax.set_title("Study area & network")

    ax.set_axis_off()

    fig.savefig(
        homepath + "/results/plots/studyarea_network.png", dpi=300, bbox_inches="tight"
    )

    plt.close()

    return None


def plot_polygon_layer(
    eval_stats, layerkey, layervalue, network_edges, config_colors, homepath
):

    # layerkey is the name of the layer
    # layervalue is a dict: layervalue["gpkg"] contains the network _within_
    #              layervalue ["bufferdistance"] contains the bufferdistance (in meters)
    # plot in color config_colors[layerkey]

    # get stats on percent within
    percent_within = np.round(
        100
        * eval_stats[layerkey]["within"]
        / (eval_stats[layerkey]["outside"] + eval_stats[layerkey]["within"]),
        1,
    )

    # get bufferdistance
    bufferdistance = layervalue["bufferdistance"]

    # plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    network_edges.plot(
        ax=ax,
        color="#D3D3D3",
        linewidth=0.8,
        linestyle="solid",
        zorder=0,
    )
    layervalue["gpkg"].plot(
        ax=ax,
        color=rgb2hex(config_colors[layerkey]),
        linewidth=1.5,
        zorder=1,
        label=f"{percent_within}%",
    )
    ax.set_title(f"{layerkey.capitalize()} within {bufferdistance}m from network")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(
        homepath + f"/results/plots/{layerkey}.png", dpi=300, bbox_inches="tight"
    )

    plt.close()

    return None


def plot_point_layer(
    eval_stats, layerkey, layervalue, network_edges, config_colors, homepath
):

    # layerkey is the layername
    # layervalue is a dict: layervalue["bufferdistance"], layervalue["gpkg_within"], layervalue["gpkg_without"]

    # get stats on percent within / outside

    percent_within = np.round(
        100 * eval_stats[layerkey]["within"] / eval_stats[layerkey]["total"], 1
    )

    percent_outside = np.round(100 - percent_within, 1)

    # get bufferdistance
    bufferdistance = layervalue["bufferdistance"]

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    network_edges.plot(
        ax=ax,
        color="#D3D3D3",
        linewidth=0.8,
        linestyle="solid",
        zorder=0,
    )

    layervalue["gpkg_outside"].plot(
        ax=ax,
        color=rgb2hex(config_colors[layerkey]),
        zorder=1,
        label=f"Outside reach ({percent_outside}%)",
        markersize=2,
        alpha=0.3,
    )

    layervalue["gpkg_within"].plot(
        ax=ax,
        color=rgb2hex(config_colors[layerkey]),
        zorder=2,
        label=f"Within reach ({percent_within}%)",
        markersize=2,
    )
    ax.set_title(f"{layerkey.capitalize()} within {bufferdistance}m from network")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(
        homepath + f"/results/plots/{layerkey}.png", dpi=300, bbox_inches="tight"
    )

    plt.close()

    return None


def plot_slopes(homepath):

    ### READ IN SLOPE VALUES
    edges_slope = gpd.read_file(homepath + "/data/output/elevation/edges_slope.gpkg")
    config_slope = yaml.load(
        open(homepath + "/config/config-slope.yml"), Loader=yaml.FullLoader
    )
    slope_ranges = config_slope["slope_ranges"]
    slope_ranges += [100]  # add max value (upper limit)
    config_color = yaml.load(
        open(homepath + "/config/config-colors-slope.yml"), Loader=yaml.FullLoader
    )
    slope_colors = config_color["slope"]
    slope_colors = [rgb2hex(c) for c in slope_colors]

    edges_slope["bucket"] = pd.cut(
        edges_slope.ave_slope, slope_ranges, include_lowest=True, labels=[0, 1, 2, 3]
    )

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    for i in range(4):
        if i < 3:
            my_label = f"{slope_ranges[i]}-{slope_ranges[i+1]}%"
        else:
            my_label = f">{slope_ranges[i]}%"
        edges_slope[edges_slope.bucket == i].plot(
            ax=ax, color=slope_colors[i], label=my_label
        )

    ax.set_title("Average slope values")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(homepath + f"/results/plots/slopes.png", dpi=300, bbox_inches="tight")

    plt.close()

    return None


def plot_components(homepath):

    comppath = homepath + "/data/output/network/components/"
    comp_files = sorted([f for f in os.listdir(comppath) if f[-5:] == ".gpkg"])
    if len(comp_files) > 0:
        comp_idx = [int(re.findall("\d+", f)[0]) for f in comp_files]
        comp_dict = {}
        for file, idx in zip(comp_files, comp_idx):
            comp_dict[idx] = gpd.read_file(comppath + file)

        layercolors = sns.color_palette("colorblind", len(comp_idx))
        comp_colors = {}
        for k, v in zip(comp_idx, layercolors):
            comp_colors[k] = (
                str([int(rgba * 255) for rgba in v]).replace("[", "").replace("]", "")
            )
        for k, v in comp_colors.items():
            comp_colors[k] = rgb2hex(v)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    for idx in comp_idx:
        comp_dict[idx].plot(ax=ax, color=comp_colors[idx], label=f"Component {idx}")

    ax.set_title("Disconnected components")
    ax.set_axis_off()
    ax.legend(loc="lower right")

    fig.savefig(
        homepath + f"/results/plots/disconnected-components.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    return None


def collapse_layer_group(group_name):

    root = QgsProject.instance().layerTreeRoot()
    nodes = root.children()

    for n in nodes:
        if isinstance(n, QgsLayerTreeGroup):
            if n.isExpanded() == True and n.name() == group_name:
                n.setExpanded(False)


def expand_layer_group(group_name):

    root = QgsProject.instance().layerTreeRoot()
    nodes = root.children()

    for n in nodes:
        if isinstance(n, QgsLayerTreeGroup):
            if n.name() == group_name and n.isExpanded() == False:
                n.setExpanded(True)


def remove_existing_group(group_name):

    root = QgsProject.instance().layerTreeRoot()
    for group in [child for child in root.children() if child.nodeType() == 0]:
        if group.name() == group_name:
            root.removeChildNode(group)


def move_layer(layer_name, position):

    # get basemap layer
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    # clone
    cloned_layer = layer.clone()

    # add clone to instance, but not map/TOC
    QgsProject.instance().addMapLayer(cloned_layer, False)

    root = QgsProject.instance().layerTreeRoot()

    # insert at bottom of TOC
    root.insertLayer(position, cloned_layer)

    # remove original
    root.removeLayer(layer)
