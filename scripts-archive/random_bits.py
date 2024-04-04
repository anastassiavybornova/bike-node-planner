# ##### PLOT HILLSHADE
# if plot_intermediate and dataforsyning_token:
#     dem_name = "dhm_terraen_skyggekort"
#     wms_url = "https://api.dataforsyningen.dk/dhm_DAF?" + f"token={dataforsyning_token}"
#     source = f"crs={proj_crs}&dpiMode=7&format=image/png&layers={dem_name}&styles&tilePixelRatio=0&url={wms_url}"

#     dem_raster = QgsRasterLayer(source, dem_name, "wms")

#     QgsProject.instance().addMapLayer(dem_raster)

#     print("added dem raster")


# if "Study area" in layer_names:
#     # Change symbol for study layer
#     draw_simple_polygon_layer(
#         "Study area",
#         color="250,181,127,0",
#         outline_color="red",
#         outline_width=0.7,
#     )

#     move_study_area_front()


# turn_off_layer_names = [
#     "Elevation values segments",
#     "Vertices",
#     "Segments",
#     "Network edges",
# ]

# turn_off_layer_names = [t for t in turn_off_layer_names if t in layer_names]

# turn_off_layers(turn_off_layer_names)
