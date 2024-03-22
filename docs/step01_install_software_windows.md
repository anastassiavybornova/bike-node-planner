## Step 1: Software installations for Windows

Follow these step-by-step instructions to set up QGIS and Python for the BikeNodePlanner on your Windows machine.

1. **Download the repository contents**: On the [landing page](hhttps://github.com/anastassiavybornova/bike-node-planner) of this repository, click on the `Code` button (in the upper right), then `Download ZIP` to download the entire repository to your local machine. Unzip the downloaded folder `bike-node-planner-main`. This will be the main folder for the entire workflow.

<p align="center"><img alt="Download the bike-node-planner-main folder" src="/docs/screenshots/github.png" width=80%></p>

**Note:** If you already work with the Git command line extension and prefer to clone the repository instead of downloading it, you need to have [`git-lfs`](https://git-lfs.com) installed on your machine before cloning. 

2. The BikeNodePlanner is developed to run with QGIS-LTR 3.28 Firenze, but might also work with later or earlier versions. If you already have QGIS installed, you can check your version by clicking on `About QGIS-LTR`, as shown below. To download the latest stable release of QGIS or to upgrade it to the 3.28 version, [click here](https://www.qgis.org/en/site/forusers/download.html). 

<p align="center"><img alt="Check your QGIS version" src="/docs/screenshots/qgis-version.png" width=80%></p>

3. Find out the path to the Python installation for the QGIS app on your local machine. That is, find the full path to the `python3X` application file located in your QGIS installation folder. Typically, this will be similar to

```
C:\Program Files\QGIS 3.28\apps\Python39\python
```

To avoid issues with permissions for the custom setup of Python packages in your QGIS installation on Windows, you will need to copy-paste the following two files,
```
libcrypto-1_1-x64.dll
libssl-1_1-x64.dll
```

* **from** the `\bin\` subfolder of your QGIS installation
* **to** the `\apps\Python39\` subfolder of your QGIS installation. 

To do so, simply 
* open your file explorer
* navigate to the path `C:\Program Files\QGIS 3.28\bin` 
* locate the 2 files and copy them 
* navigate to the path `C:\Program Files\QGIS 3.28\apps\Python39\` and 
* paste the 2 files here. 

**Note** that the exact file paths might look slightly different on your machine (e.g. a different QGIS version number, or a different Python version number).

4. Open your command line interface (Command Prompt on Windows)

5. Use the path from step 3 (abbreviated as `<qgispythonpath>` below) to run the commands below in your commmand line interface. (Copy each line below separately, paste it in your command line interface, replace `<qgispythonpath>` in quotation marks by the path from step 3, and hit enter.) Note that you have to be connected to the internet for the installs to work.
```
"<qgispythonpath>" -m pip install --upgrade shapely
"<qgispythonpath>" -m pip install --upgrade geopandas --force-reinstall -v geopandas==0.14.0
"<qgispythonpath>" -m pip install momepy
"<qgispythonpath>" -m pip install osmnx==1.6.0
"<qgispythonpath> -m pip install numpy --force-reinstall -v numpy==1.22.4"
"<qgispythonpath>" -m pip install contextily
```

Alternatively, if you know [how to run a bash script](https://linuxhandbook.com/run-bash-script/), navigate `bike-node-planner-main` folder in your command line interface and run `./setuppython.sh <qgispythonpath>`.

<p align="center"><img alt="Setting up PyQGIS from the command line (Command Prompt on Windows)" src="/docs/screenshots/cli-install-windows.png" width=80%></p>

6. If you had QGIS open, restart QGIS now for the changes to take effect.