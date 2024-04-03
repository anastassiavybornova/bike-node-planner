# Step 3: Customize your user settings

Provide the following user settings by editing and saving the `.yml` files, found in the main folder `bike-node-planner-main`:

* in `config.yml`: a projected CRS for your study area
* in `config-point.yml`: distance thresholds (in meters) for each point layer in `/data/input/point/`
* in `config-polygon.yml`: buffer distances (in meters) for each polygon layer in `/data/input/polygon/`

**Optionally**, you can also customize the following default settings:
* in `config-slope.yml`: the segment length and the slope ranges used for computation of elevation for the network
* in `config-colors-eval.yml`: colors used for plotting all evaluation layers from `/data/input/point/` and `/data/input/polygon/`
* in `config-colors-slope.yml`: colors used for plotting the slope ranges