# BDMG-project

Authors: 
- Ferrari Sara ([github profile](https://github.com/saraferrari))
- Pavone Cosimo ([github profile](https://github.com/cosimop2000))
- Pederzoli Sara ([github profile](https://github.com/sarapeddy))

# Dataset

This dataset includes nationwide traffic crash information for all 49 US states. The dataset has been continously assembled since February 2016, using data from multiple sources, including several APIs that stream traffic incident data. These APIs capture traffic incidents reported by various entities, such as US and state departments of transportation, law enforcement agencies, traffic cameras and road network sensors. The dataset currently contains over 7 milion records. 


# Procedure 

The project goal is to identify the best libraries to perform performance analysis on a single local machine. The followed pipeline is specified by a JSON file and it is inspired by this [notebook](https://www.kaggle.com/code/michaelbryantds/eda-of-vehicle-accident-data) on Kaggle. The libreries considered are pandas, modin(_ray, _dask), polars, pyspark_pandas, vaex, datatable and spark.
The dataset files, including the JSON files, should be placed in the `datasets` folder at the root of this project, inside US_Accidents_March23. 

The analysis is made of 3 steps:

1. Run every command to compute the execution time for each of them:
```
python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --locally
```

2. Run all the pipeline to compute the total time of execution:
```
python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --pipeline --locally
```

3. Run every pipeline step to compute the execution time for of them:
```
python3 run_algorithm.py --algorithm <algorithm_name> --dataset <dataset_name> --pipeline-step --locally
```

# Result
The result obtained are the following:

1. The execution time for each command is the following:
   
   ![methods time](https://github.com/cosimop2000/BDMG-vehicle-accidents/blob/master/assets/images/output1_10.png)
  
3. The execution time for each pipeline step is the following:
   
   ![steps time](https://github.com/cosimop2000/BDMG-vehicle-accidents/blob/master/assets/images/output2_10.png)
   
5. The total execution time for each library is the following:

   ![total time](https://github.com/cosimop2000/BDMG-vehicle-accidents/blob/master/assets/images/output3_10.png)




# References

The core part of the project is taken by [this repo](https://github.com/dbmodena/bento). Some methods are being added and modified for our specific use case.
