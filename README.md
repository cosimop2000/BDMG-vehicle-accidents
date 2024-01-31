# BDMG-project

Authors: Ferrari Sara, Pavone Cosimo, Pederzoli Sara

# Dataset

This dataset includes nationwide traffic crash information for all 49 US states. The dataset has been continously assembled since February 2016, using data from multiple sources, including several APIs that stream traffic incident data. These APIs capture traffic incidents reported by various entities, such as US and state departments of transportation, law enforcement agencies, traffic cameras and road network sensors. The dataset currently contains over 7 milion records. 


# Procedure 

The dataset files, including the JSON files, should be placed in the `datasets` folder at the root of this project, inside US_Accidents_March23.

To run

python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --locally

python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --pipeline --locally

python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --pipeline-step --locally
