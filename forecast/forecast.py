# this class is only for el_salvador

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
import pymongo

client = pymongo.MongoClient("mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/WattTime?retryWrites=true&w=majority")

db = client['El_Salvador']
col = db['Historic']
doc = col.find_one({'00-01/01/2019.0.type':'Biomass'})

# find or find_one selects documents that have Biomass in them so we are just selecting all documents?
# need to use different query?



# find({})[0] index 0 is first document
# find({})[1] is index 1 which is week 2 second document
print(doc)

# how to query data 
# create data structures to hold this data
# bin_dates?, hour, type, target feature

# gradient booster regressor
# https://towardsdatascience.com/using-gradient-boosting-for-time-series-prediction-tasks-600fac66a5fc

# [bin_date, hour, type, target feature]
# [bin_date, hour, type, target feature]
