# BikeNodePlanner

*A Decision Support Tool for Bicycle Node Networks*

<p align="center"><img alt="The Cycle Node Network Planner" src="/img/social-preview.png" width=100%></p>

The BikeNodePlanner is an open-source, customizable, data-driven decision support tool for bicycle node network planning. The BikeNodePlanner runs in QGIS and Python. It can be used for any study area in the world.

The tool takes as input:

1. a preliminary network plan, and 
2. one or several additional layers of relevant geospatial data within the study area to be used for evaluation;

and provides the user with a network analysis (based on the network topology of the preliminary network plan) and a customizable evaluation of the network (based on the additional geospatial data layers). Both can be explored interactively in QGIS. The BikeNodePlanner highlights areas where the network might need to be adjusted, and helps inform further planning decisions.

The BikeNodePlanner originates from a collaboration between [Dansk Kyst- og Naturturisme](https://www.kystognaturturisme.dk) (DKNT) and the [IT University of Copenhagen](https://nerds.itu.dk) as part of the project [Bedre vilkår for cykelturismen in Denmark](https://www.kystognaturturisme.dk/cykelknudepunkter), where the goal was to develop a country-wide bicycle node network for Denmark. 

The BikeNodePlanner is introduced in the forthcoming research paper "The BikeNodePlanner: a data-driven decision support tool for bicycle node network planning".

<!-- , currently available as preprint:

> Vybornova A, Vierø A, Szell M (2024) The BikeNodePlanner: a data-driven decision support tool for bicycle node network planning. arXiv: LINK

Anastassia Vybornova<sup>1</sup>, Ane Rahbek Vierø<sup>1</sup>, Michael Szell<sup>1,2,3</sup>

1 NEtworks, Data and Society (NERDS), Computer Science Department, IT University of Copenhagen, anvy@itu.dk

2 ISI Foundation, 10126, Turin, Italy

3 Complexity Science Hub Vienna, 1080, Vienna, Austria -->

***

# Instructions

To use the BikeNodePlanner, follow the detailed step-by-step instructions below.

## Step 1: Download the contents of this repository

[Download](https://github.com/anastassiavybornova/bike-node-planner-data-denmark/archive/refs/heads/main.zip) or `git clone` the contents of this repository to your local machine.

## Step 2: Software installations

Set up the BikeNodePlanner environment on your machine. Detailed instructions depend on your operating system:

* [macOS/linux: step02_install_software_macos](./docs/step02_install_software_macos.md)
* [Windows: step02_install_software_windows](./docs/step02_install_software_windows.md)

## Step 3: Prepare your data

Prepare your input data for the BikeNodePlanner:

* the bicycle node network that you want to evaluate
* the geospatial data for the evaluation

Detailed instructions: [./docs/step03_prepare_data.md](./docs/step03_prepare_data.md).

## Step 4: Customize your user settings

Customize the BikeNodePlanner analysis by providing your preferred user settings. Detailed instructions: [./docs/step04_customize_settings.md](./docs/step04_customize_settings.md).

## Step 5: Create an empty project in QGIS

Open QGIS and create an empty project, then save it in the main folder of this repository (which you downloaded at Step 1), i.e., in the `bike-node-planner` folder.

## Step 6: Run the BikeNodePlanner evaluation in QGIS, and explore results!

Now, the fun begins! Run the BikeNodePlanner evaluation in QGIS, and explore the results. Detailed instructions: [./docs/step06_run_evaluation.md](./docs/step06_run_evaluation.md).

***

# Getting in touch

Questions, comments, feedback? You can reach out to us by email: [anvy@itu.dk](mailto:anvy@itu.dk)