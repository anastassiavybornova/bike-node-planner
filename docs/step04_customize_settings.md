# Step 4: Customize your user settings

Provide the following user settings by editing and saving the `.yml` files, found in the config folder `bike-node-planner/config`:

* in `config.yml`: a projected CRS for your study area (default is set to "EPSG:25832" for Denmark)
* in `config-point.yml`: distance thresholds (in meters) for each point layer in `/data/input/point/` (for the 3 example layers "facility", "poi", and "service", default is set to 100m, 750m and 1500m, respectively)
* in `config-polygon.yml`: buffer distances (in meters) for each polygon layer in `/data/input/polygon/` (for the 5 example layers "agriculture", "culture", "nature", "sommerhouse", and "verify", default is set to 50m, 100m, 200m and 250m, respectively)

**Optionally**, you can also customize the following default settings:

For [script02](../docs/step06_run_evaluation.md#script02py-network-evaluation) outputs, 
* in `config-colors-eval.yml`: colors used for plotting all evaluation layers from `/data/input/point/` and `/data/input/polygon/`

For [script03](../docs/step06_run_evaluation.md#script03py-elevation-slope) outputs,
* in `config-slope.yml`: the segment length and the slope ranges used for computation of elevation for the network
* in `config-colors-slope.yml`: colors used for plotting the slope ranges

For [script05](../docs/step06_run_evaluation.md#script05py-edge-length-classification) and [script06](../docs/step06_run_evaluation.md#script06py-loop-length-classification):
* in `config-topological-analysis.yml`: the length ranges for edge length analysis and loop length analysis

For scripts 01-06:
* in `config-display.yml`: for each of the evaluation layers, decide whether they should be displayed in QGIS by default