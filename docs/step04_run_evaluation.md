# Step 4: Run the BikeNodePlanner evaluation in QGIS, and explore results

After having installed the necessary software (Step 01), prepared your input data (Step 02), and customized your user settings (Step 03), you can now run the BikeNodePlanner analysis in QGIS. 

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
8. While the script is running, you will see status messages in the console window.
9. Once you see the message `Script XXX ended succcessfully`, save the project (`cmd+s`), and run the next script. 

<p align="center"><img alt="Running the scripts in the QGIS Python console" src="/docs/screenshots/qgis-run.png" width=80%></p>

**Troubleshooting**
* Note that QGIS might become unresponsive for several minutes while a script is running. 
* At any stop in the workflow, you can save the QGIS project, close it, and then come back to it later.
* Note that for some of the scripts, a stable internet connection is required.
* If the `script04.py` (slope computation) script fails to run - please try again! (it sometimes requires several attempts)
* if a script fails to complete and throws an error message: 
    * save, close, and reopen the QGIS project
    * try to run the script again
    * if the problem persists: create a new QGIS project in the `bike-node-planner-main` folder and restart the workflow there from script 00

***

## The BikeNodePlanner scripts: Output and interpretation

The BikeNodePlanner consists of several scripts, which have to be run in the specified order. Below, you find explanations on each scripts' analysis, output, and how to interpret the corresponding results.

### `script00.py`: Checking for correctness of all data

**TODO** script00 checks for correctness of all data

### `script01.py`: Plotting the study area

script01 plots study area and a basemap from OpenStreetMap

### `script02.py`: 

script02 makes and plots the network

**TODO update description, refer & link to technical v communication stuff**

### `script03.py`: 

script03 makes and plots evaluation (point/polygon/linestring)

Explore the results of the evaluation by (de)selecting layers in the QGIS project. 

For example, select "Culture/Network in culture areas" within the "Evaluate network" layer to explore which parts of the network lead through culturally particularly interesting parts of the study area.

Or, select "POIS" within the "Evaluate network" layer to explore which points of interest are within vs. outside reach (dark vs. light color) of the network. Use the "Identify features" tool to get more information on a particular feature on the map.

**TODO update above description to fit the current setup; insert screenshots**

### `script04.py`: 

script04 makes and plots elevation (slope)

**TODO insert explanation and screenshots**

### `script05.py`: 

script05 makes and plots network statistics & disconnected components

**TODO insert explanation and screenshots**

### `script06.py`: 

script06 generates summary statistics plots in `results/plots/*.png`

After running this script, you will find a plot of summary statistics in the subfolder `results/plots/` (in your `bike-node-planner-main` folder): 
**TO DO INSERT EXAMPLE IMAGES**