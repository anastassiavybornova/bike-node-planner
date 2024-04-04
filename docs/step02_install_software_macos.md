# Step 1: Install software for macOS

Follow these step-by-step instructions to set up QGIS and Python for the BikeNodePlanner on your macOS machine.

***

1. The BikeNodePlanner is developed to run with QGIS-LTR 3.28 Firenze, but might also work with later or earlier versions. If you already have QGIS installed, you can check your version by clicking on `About QGIS-LTR`, as shown below. To download the latest stable release of QGIS or to upgrade it to the 3.28 version, [click here](https://www.qgis.org/en/site/forusers/download.html). 

<p align="center"><img alt="Check your QGIS version" src="/docs/screenshots/qgis-version.png" width=80%></p>

<!-- Troubleshooting: if new installation on Mac, must be first opened 1x with rightclick and confirm -->

***

2. Find out the path to the Python installation for the QGIS app on your local machine. That is, find the full path to the `python3.X` application file located in your QGIS installation folder. Typically, this will be similar to

```
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3.9
```

***

3. Open your command line interface (Terminal on macOS)

***

4. Use the path from step 3 (abbreviated as `<qgispythonpath>` below) to run the commands below in your commmand line interface. (Copy each line below separately, paste it in your command line interface, replace `<qgispythonpath>` by the path from step 3, and hit enter.) Note that you have to be connected to the internet for the installs to work.

```
<qgispythonpath> -m pip install --upgrade shapely  
<qgispythonpath> -m pip install --upgrade geopandas --force-reinstall -v geopandas==0.14.0
<qgispythonpath> -m pip install momepy
<qgispythonpath> -m pip install osmnx==1.6.0
<qgispythonpath> -m pip install numpy --force-reinstall -v numpy==1.22.4
<qgispythonpath> -m pip install contextily
<qgispythonpath> -m pip install --upgrade lxml
```

<p align="center"><img alt="Setting up PyQGIS from the command line (Terminal on MacOS)" src="/docs/screenshots/cli-install-macos.png" width=80%></p>

Alternatively, if you know [how to run a bash script](https://linuxhandbook.com/run-bash-script/), navigate to `bike-node-planner-main` folder in your command line interface and run 
```
./setuppython.sh <qgispythonpath>
```

***

5. If you had QGIS open, restart QGIS now for the changes to take effect.