# Step 2: Install software for macOS

Follow these step-by-step instructions to set up QGIS and Python for the BikeNodePlanner on your macOS machine.

***

* The BikeNodePlanner is developed to run with QGIS-LTR 3.34 Prizren, but might also work with later or earlier versions. If you already have QGIS installed, you can check your version by clicking on `About QGIS-LTR`, as shown below. To download the latest stable release of QGIS or to upgrade it to the 3.34 version, see [https://www.qgis.org/en/site/forusers/download.html](https://www.qgis.org/en/site/forusers/download.html).

<!-- Troubleshooting: if new installation on Mac, must be first opened 1x with rightclick and confirm -->

***

* Find out the path to the Python installation for the QGIS app on your local machine. That is, find the full path to the `python3.X` application file located in your QGIS installation folder. Typically, this will be similar to:

```bash
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3.9
```

***

* Open your command line interface (Terminal on macOS) and navigate to the main folder of the BikeNodePlanner repository.

***

* From the command line, run the bash script `install_pyqgis.sh`, replacing `<qgispythonpath>` with your Python installation path (see above):

```bash
bash install_pyqgis.sh --python_path <qgispythonpath>
```

***

* If you had QGIS open, restart QGIS now for the changes to take effect.