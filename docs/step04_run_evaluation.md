# Step 4: Run the BikeNodePlanner evaluation in QGIS, and explore results

After having installed the necessary software ([Step 01](../README.md#step-1-software-installations)), prepared your input data ([Step 02](../README.md#step-2-prepare-your-data)), and customized your user settings ([Step 03](../README.md#step-3-customize-your-user-settings)), you can now run the BikeNodePlanner analysis in QGIS. 

There are several analysis steps. For each step, you need to run one Python script in QGIS. The Python scripts are located in `/bike-node-planner-main/scripts/`. Running each script produces some visual output in your QGIS project, and/or plots and statistics that will be saved to your local machine.

Below, you find:
* first, general instructions on how to run a Python script in QGIS;
* then, for each script of the BikeNodePlanner, explanations of its output and how to interpret it.

***

## Running a Python script in QGIS

In QGIS,

1. Open the Python Console 
2. Click on `Show Editor`
3. Click on `Open Script`
4. Navigate to the `scripts` subfolder (within the `bike-node-planner-main` folder) 
5. Select the next script (by number: 01, then 02, ...)
6. Click on `Open`
7. Click on `Run`.
8. While the script is running, check the console window for status messages.
9. Once you see the message `Script XXX ended succcessfully` in the console window, save the project (disquette icon or `cmd+s`), and run the next script.

<p align="center"><img alt="Running the scripts in the QGIS Python console" src="/docs/screenshots/qgis-run.png" width=80%></p>

## Troubleshooting

* Note that QGIS might become unresponsive for several minutes while a script is running. 
* At any stop in the workflow, you can save the QGIS project, close it, and then come back to it later.
* Note that for some of the scripts, a stable internet connection is required.
* If the `script03.py` (slope computation) script fails to run - please try again! (it sometimes requires several attempts)
* if a script fails to complete and throws an error message: 
    * save, close, and reopen the QGIS project
    * try to run the script again
    * if the problem persists: create a new QGIS project in the `bike-node-planner-main` folder and restart the workflow there from script 00

***

# The BikeNodePlanner scripts: Output and interpretation

The BikeNodePlanner consists of several scripts, which have to be run in the specified order. Below, you find explanations on each scripts' analysis, output, and how to interpret the corresponding results.

## `script00.py`: Sanity check of all input data

**TODO** script00 checks for correctness of all data

## `script01.py`: Visualization of the study area

script01 plots the study area and a basemap from OpenStreetMap, and extracts the input network data to only include features that intersect with the study area.

## `script02.py`: Evaluation with point and polygon layers

script02 uses the point and polygon layers provided in `/data/input/point/` and `/data/input/polygon/` to evaluate the network. 

For each point layer, the BikeNodePlanner checks whether the points are within or outside of reach, based on the maximum distance defined by the user in `config-point.yml`. For each polygon layer, the BikeNodePlanner finds the parts of the network that run _through_ the layer, including a buffer distance defined by the user in `config-polygon.yml`. 

You can explore the results of the evaluation by (de)selecting layers in the QGIS project. For example, if you have provided a polygon layer `nature.gpkg`, you can now select "Nature/Network in nature areas" within the "Evaluate network" layer to explore which parts of the network run through the nature layer. Or, if you have provided a point layer `museums.gpkg`, you can now select "Museums" within the "Evaluate network" layer to explore which museums within vs. outside reach (dark vs. light color) of the network. 

To get more information on a particular feature on the map, use the ["Identify features"](https://docs.qgis.org/3.34/en/docs/user_manual/introduction/general_tools.html#identify) tool in QGIS.

**TODO update above description to fit the current setup; insert screenshots**

## `script03.py`:

script03 makes and plots elevation (slope)

**TODO insert explanation and screenshots**

## `script04.py`:

script04 makes and plots network statistics & disconnected components

**TODO insert explanation and screenshots**

## `script05.py`:

script05 generates summary statistics plots in `results/plots/*.png`

After running this script, you will find a plot of summary statistics in the subfolder `results/plots/` (in your `bike-node-planner-main` folder):
**TO DO INSERT EXAMPLE IMAGES**
