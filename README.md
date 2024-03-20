# bike-node-planner

## prepare QGIS & Python environment

as for [knudepunkter](https://github.com/anastassiavybornova/knudepunkter) (for the future, possibly in docker?)

## prepare data

* download/clone this repo
* provide data in `./data/input/` (if Denmark: data preprocessing is automatized, see [data-denmark repo](https://github.com/anastassiavybornova/bike-node-planner-data-denmark))
* provide user settings in `./config-X.yml`

## run scripts in QGIS

* **TODO** script00 checks for correctness of all data
* script01 plots study area
* script02 makes and plots communication network
* script03 makes and plots evaluation (point/polygon/linestring)
* script04 makes and plots elevation (slope)
* script05 makes and plots network statistics & disconnected components
* script06 generates summary statistics plot in `results/plots/*.png`