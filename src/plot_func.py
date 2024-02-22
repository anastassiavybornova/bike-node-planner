from random import randrange
# from qgis.core import QgsVectorLayer
from qgis.core import *

def move_study_area_front(layer_name="Study area"):
    # get basemap layer
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    # clone
    cloned_layer = layer.clone()

    # add clone to instance, but not map/TOC
    QgsProject.instance().addMapLayer(cloned_layer, False)

    root = QgsProject.instance().layerTreeRoot()

    # insert at bottom of TOC
    root.insertLayer(0, cloned_layer)

    # remove original
    root.removeLayer(layer)

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


def remove_existing_layers(layer_name_list):
    clean_layer_names = [l.replace(" ", "_") for l in layer_name_list]
    clean_layer_names = [l.replace("(", "_") for l in clean_layer_names]
    clean_layer_names = [l.replace(")", "_") for l in clean_layer_names]
    clean_layer_names = [l.replace("/", "_") for l in clean_layer_names]
    clean_layer_names = [l.replace(":", "_") for l in clean_layer_names]
    clean_layer_names = [l.replace("-", "_") for l in clean_layer_names]

    existing_layers_ids = [
        layer.id() for layer in QgsProject.instance().mapLayers().values()
    ]

    remove_layers = [
        e for e in existing_layers_ids if e.startswith(tuple(clean_layer_names))
    ]

    for r in remove_layers:
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
 
    slope_ranges += [100] # add max value (upper limit)
    # make pairs of upper-lower limits for ranges
    slope_pairs = [list(pair) for pair in zip(slope_ranges, slope_ranges[1:])]

    slope_names = [
        f"{slope_pairs[0][0]}-{slope_pairs[0][1]}% (manageable elevation)", 
        f"{slope_pairs[1][0]}-{slope_pairs[1][1]}% (noticeable elevation)", 
        f"{slope_pairs[2][0]}-{slope_pairs[2][1]}% (steep elevation)", 
        f">{slope_pairs[3][0]}% (very steep elevation)"
        ]
   
    # to make sure upper and lower limit are not identical for disparate ranges:
    for i in range(len(slope_pairs)-1):
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