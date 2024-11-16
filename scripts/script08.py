# ***** Export layouts *****

from qgis.core import *
from qgis.utils import *

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

# load custom functions
exec(open(homepath + "/src/plot_func.py").read())

# Choose whether to export the layouts
export = True

# Based on based on https://www.geodose.com/2022/02/pyqgis-tutorial-automating-my_map-layout.html
# and https://gis.stackexchange.com/questions/427905/create-my_map-layout-focused-on-selected-feature-using-pyqgis

# NOTE Fill out layout dictionary with layout name/types as keys and the list of all layers that should be displayed in the layout as values
layout_dict = {
    "input_data": ["Study area", "Network edges"],
    "agriculture": ["agriculture areas", "Network in agriculture areas"],
    "nature": ["nature areas", "Network in nature areas"],
    "verify": ["verify areas", "Network in verify areas"],
    "summerhouse": ["summerhouse areas", "Network in summerhouse areas"],
    "culture": ["culture areas", "Network in culture areas"],
    "facilities": [
        "facility within reach",
        "facility outside reach",
    ],
    "services": [
        "service within reach",
        "service outside reach",
    ],
    "points_of_interest": [
        "poi within reach",
        "poi outside reach",
    ],
    "edge_length": [
        "too long edges",
        "too short edges",
        "ideal range edges",
        "above ideal edges",
    ],
    "loop_length": ["too long loops", "too short loops", "ideal range loops"],
    "slope": ["Segments slope"],
}

# add all component layers to the list of layers
all_layers = QgsProject.instance().mapLayers().values()
component_layer_names = [
    layer.name() for layer in all_layers if "Component" in layer.name()
]
layout_dict["disconnected_components"] = component_layer_names


# Define map extent and ratio
layers_for_plotting = []
for list in layout_dict.values():
    layers_for_plotting.extend(list)

all_layers = QgsProject.instance().mapLayers().values()
all_layers_bbox = [
    layer
    for layer in all_layers
    if "Basemap" not in layer.name() and layer.name() in layers_for_plotting
]
bbox = find_largest_bbox(all_layers_bbox)

bbox.grow(1500)  # add some padding to the bbox

bbox_ratio = bbox.height() / bbox.width()

resize_val1, resize_val2 = 180, 180 * bbox_ratio

for layout_name, layout_layer_names in layout_dict.items():

    # Turn all layers off as default
    all_layer_names = [
        layer.name() for layer in QgsProject.instance().mapLayers().values()
    ]
    turn_off_layers(all_layer_names)

    # Always include basemap and network edges
    layout_layer_names.extend(["Basemap", "Network edges"])

    # Check that all desired layers exists
    turn_on_layer_names = [l for l in layout_layer_names if l in all_layer_names]

    non_existing_layer_names = [
        l for l in layout_layer_names if l not in all_layer_names
    ]
    for l in non_existing_layer_names:
        print(f"Skipping layer '{l}' - does not exist in the project")

    # Turn layers in list on
    turn_on_layers(turn_on_layer_names)

    # Remove layout if already exists
    remove_layout(layout_name)

    project = QgsProject.instance()
    manager = project.layoutManager()

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    manager.addLayout(layout)

    # create the map
    my_map = QgsLayoutItemMap(layout)
    my_map.setRect(20, 20, 20, 20)

    map_settings = QgsMapSettings()

    # set extent of map to the bounding box of the study area
    map_settings.setExtent(bbox)
    my_map.setExtent(bbox)

    my_map.setBackgroundColor(QColor(255, 255, 255, 0))
    layout.addLayoutItem(my_map)

    # my_map.attemptMove(QgsLayoutPoint(5, 5, QgsUnitTypes.LayoutMillimeters))
    my_map.attemptResize(
        QgsLayoutSize(resize_val1, resize_val2, QgsUnitTypes.LayoutMillimeters)
    )

    output_path = homepath + "/results/plots/"
    exporter = QgsLayoutExporter(layout)

    if export:
        img_path = output_path + f"{layout_name}_qgis.png"
        image_export_settings = QgsLayoutExporter.ImageExportSettings()
        image_export_settings.cropToContents = True
        image_export_settings.dpi = 300
        exporter.exportToImage(img_path, image_export_settings)
