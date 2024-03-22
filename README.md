# BikeNodePlanner

*A Decision Support Tool for Bicycle Node Networks*

<p align="center"><img alt="The Cycle Node Network Planner" src="/img/social-preview.png" width=100%></p>

The BikeNodePlanner is an open-source, customizable, data-driven decision support tool for bicycle node network planning. The BikeNodePlanner runs in QGIS and Python. It can be used for any study area in the world. 

The tool takes as input:
1. a preliminary network plan, and 
2. one or several additional layers of relevant geospatial data within the study area to be used for evaluation;
and provides the user with a network analysis (based on the network topology of the preliminary network plan) and a customizable evaluation of the network (based on the additional geospatial data layers). Both can be explored interactively in QGIS. The BikeNodePlanner highlight areas where the network might need to be adjusted, and helps inform further planning decisions.

The BikeNodePlanner originates from a collaboration between [Dansk Kyst- og Naturturisme](https://www.kystognaturturisme.dk) (DKNT) and the [IT University of Copenhagen](https://nerds.itu.dk) as part of the project [Bedre vilkår for cykelturismen in Denmark](https://www.kystognaturturisme.dk/cykelknudepunkter), whose goal it was to develop a country-wide bicycle node network for Denmark. 

The BikeNodePlanner is introduced in the forthcoming research paper "The BikeNodePlanner: a data-driven decision support tool for bicycle node network planning", currently available as [arxiv preprint](link here). 

> Vybornova A, Vierø A, Szell M (2024) The BikeNodePlanner: a data-driven decision support tool for bicycle node network planning. arXiv: LINK

Anastassia Vybornova<sup>1</sup>, Ane Rahbek Vierø<sup>1</sup>, Michael Szell<sup>1,2,3</sup>

1 NEtworks, Data and Society (NERDS), Computer Science Department, IT University of Copenhagen, anvy@itu.dk

2, 3 Michael's further affiliations

# Instructions

To use the BikeNodePlanner, follow the detailed step-by-step instructions below. 

## Step 1: Software installations

First, set up the BikeNodePlanner environment on your machine. Detailed instructions are [here](./docs/step01_install_software.md).

## Step 2: Prepare your data

Second, prepare your input data for the BikeNodePlanner:
* the bicycle node network that you want to evaluate
* the geospatial data for the evaluation

Detailed instructions are [here](./docs/step02_prepare_data.md).

## Step 3: Customize your user settings

Third, customize the BikeNodePlanner analysis by providing your preferred user settings. Detailed instructions are [here](./docs/step03_customize_settings.md).

## Step 4: Run the BikeNodePlanner evaluation in QGIS, and explore results!

Fourth, the fun begins! Now you can run the BikeNodePlanner evaluation in QGIS, and explore the results. Detailed instructions are [here](./docs/step04_run_evaluation.md).