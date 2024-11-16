# ***** CHECKING INPUT DATA *****

import os
import yaml
import geopandas as gpd

# define homepath variable (where is the qgis project saved?)
homepath = QgsProject.instance().homePath()

### CHECK THAT FILES EXIST

print("\n *** Checking input files... ***")

config_folder = homepath + "/config/"

input_folder = homepath + "/data/input/"

filedict_required = {
    "configuration": config_folder + "config.yml",
    "study area": input_folder + "studyarea/studyarea.gpkg",
    "network edges": input_folder + "network/processed/edges.gpkg",
}

filedict_optional = {
    "point": "folder not provided, will not evaluate point data in script02",
    "polygon": "folder not provided, will not evaluate polygon data in script02",
    "dem/dem.tif": "file not provided, will not evaluate elevation data in script03",
}

for k, v in filedict_required.items():
    assert os.path.exists(v), f"{v} file missing, please provide file before continuing!"

for k, v in filedict_optional.items():
    if not os.path.exists(input_folder + k):
        print(input_folder + k + " " + v)

print("Input files checked. \n")

# CHECK THAT PROJECTED CRS IS PROVIDED & THAT CRS IS THE SAME FOR ALL GPKGS

print("*** Checking CRS... ***")

config = yaml.load(open(config_folder + "config.yml"), Loader=yaml.FullLoader)
assert config, "Empty config file - please provide before continuing!"
try:
    proj_crs = config["proj_crs"]
except:
    raise UserWarning("Projected CRS missing in config.yml file, please provide before continuing!")
del config

gdfs = {}

gpkg_folders = [
    input_folder + "studyarea/",
    input_folder + "network/processed/",
    input_folder + "point/",
    input_folder + "polygon/"
]

for folder in gpkg_folders:
    if os.path.exists(folder):
        folder_contents = os.listdir(folder)
        folder_gpkgs = [f for f in folder_contents if f[-5:]==".gpkg"]
        if folder_gpkgs:
            for gpkg in folder_gpkgs:
                gdfs[gpkg] = gpd.read_file(folder + gpkg)

my_crs = gdfs["studyarea.gpkg"].crs  
for k, v in gdfs.items():
    assert v.crs == my_crs, f"{k} is in a different CRS than the study area. Please provide {k} in {my_crs} before continuing."

print("CRS checked. \n")

# EVALUTION LAYERS

# config-point and config-polygon:
# for each evaluation layer (both point and polygon), a buffer must be provided in the corresponding config file 
# (./config-X.yml with Ykeys in dict; and ./data/input/X/Y.yml)

geoms = ["point", "polygon"]
for geom in geoms:
    if os.path.exists(input_folder + geom):
        print(f"*** Checking configurations for {geom} layers... ***")
        config = yaml.load(open(config_folder + f"config-{geom}.yml"), Loader=yaml.FullLoader)
        files = [f.replace(".gpkg", "") for f in os.listdir(input_folder + geom) if f[-5:]==".gpkg"]
        for f in files:
            assert f in config, f"Buffer configuration for {f} missing in config-{geom}.yml file, please provide before continuing!"
        print(f"Configurations for {geom} layers checked. \n")

# SLOPES
if os.path.exists(input_folder + "dem/dem.tif"):
    print("*** Checking config-slope.yml file... ***")
    config = yaml.load(open(config_folder + "config-slope.yml"), Loader=yaml.FullLoader)
    assert config, "Empty config-slope.yml file - please provide before continuing!"
    segment_length = config["segment_length"]
    slope_ranges = config["slope_ranges"]
    assert segment_length > 0, "Segment length cannot be < 0. Please provide valid segment length in config-slope.yml before continuing"
    assert len(slope_ranges) == 4 and sorted(slope_ranges)==slope_ranges, "Please provide valid slope ranges in [0, a, b, c] format in config-slope.yml before continuing"
    del config
    print("config-slope.yml file checked. \n")

# EDGE LENGTHS AND LOOP LENGTHS
print("*** Checking config-topological-analysis.yml file... ***")
config = yaml.load(open(config_folder + "config-topological-analysis.yml"), Loader=yaml.FullLoader)
assert config, "Empty config-topological-analysis.yml file - please provide before continuing!"

ideal_length_range = config["ideal_length_range"]
max_length = config["max_length"]
loop_length_range = config["loop_length_range"]

assert ideal_length_range==sorted(ideal_length_range), "Please provide a valid length range before continuing!"
assert max_length >= ideal_length_range[-1], "Maximum length cannot be smaller than ideal length upper threshold. Please provide a valid maximum length before continuing!"
assert loop_length_range==sorted(loop_length_range), "Please provide a valid loop length range before continuing!"

print("config-topological-analysis.yml file checked.\n")

print("Done! You can now run script01.py.")