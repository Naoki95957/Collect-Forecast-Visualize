# this class is only for el_salvador

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymongo

client = pymongo.MongoClient("mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/WattTime?retryWrites=true&w=majority")
db = client['El_Salvador']
collection = db['Historic']
cursor = collection.find({})

data= []
for doc in cursor:
    doc.pop('_id')
    for key in doc:
        temp = []
        temp.append(key)
        for value in doc[key]:
            if value['type'] == 'Solar':
                temp.append(value['value'])
        if len(temp) < 2:
            temp.append(0)
        data.append(temp)