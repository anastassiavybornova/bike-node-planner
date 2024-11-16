# ***** CHECKING INPUT DATA *****

import os
import yaml

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

### CHECK THAT FILES EXIST

config_folder = homepath + "/config/"

input_folder = homepath + "/data/input/"

filedict_required = {
    "configuration": config_folder + "config.yml",
    "study area": input_folder + "studyarea/studyarea.gpkg",
    "network edges": input_folder + "network/processed/edges.gpkg",
}

filedict_optional = {
    "point": "folder missing, will not evaluate point data in script02",
    "polygon": "folder missing, will not evaluate polygon data in script02",
    "dem/dem.tif": "file missing, will not evaluate elevation data in script03",
}

for k, v in filedict_required.items():
    assert os.path.exists(v), f"{v} file missing, please provide file before continuing!"

for k, v in filedict_optional.items():
    if not os.path.exists(input_folder + k):
        print(input_folder + k + " " + v)

# CHECK THAT PROJECTED CRS IS PROVIDED
config = yaml.load(open(config_folder + "config.yml"), Loader=yaml.FullLoader)
assert config, "Empty config file - please provide before continuing!"
try:
    proj_crs = config["proj_crs"]
except:
    raise UserWarning("Projected CRS missing in config.yml file, please provide before continuing!")
del config


# EVALUTION LAYERS

# config-point and config-polygon:
# for each evaluation layer (both point and polygon), a buffer must be provided in the corresponding config file 
# (./config-X.yml with Ykeys in dict; and ./data/input/X/Y.yml)

geoms = ["point", "polygon"]
for geom in geoms:
    if os.path.exists(input_folder + geom):
        config = yaml.load(open(config_folder + f"config-{geom}.yml"), Loader=yaml.FullLoader)
        files = [f.replace(".gpkg", "") for f in os.listdir(input_folder + geom)]
        for f in files:
            assert f in config, f"Buffer configuration for {f} missing in config-{geom}.yml file, please provide before continuing!"

# SLOPES

# EDGE LENGTHS AND LOOP LENGTHS

# 

print("OK")