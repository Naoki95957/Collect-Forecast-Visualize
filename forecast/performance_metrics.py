from os.path import join
import numpy as np
import copy
from numpy.core.numeric import False_, full
import pandas as pd
from pandas.core.frame import DataFrame
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from fbprophet import Prophet
from pymongo.common import TIMEOUT_OPTIONS
import subprocess
import sys
import time
import pickle
import os

class Performance_Metrics:

    client = pymongo.MongoClient(
        "mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/" +
        "WattTime?retryWrites=true&w=majority"
        )

    metas = {'El_Salvador' : ['Biomass','Geothermal','HydroElectric','Interconnection','Thermal','Solar','Wind'],
             'Costa_Rica' : ['Hydroelectric','Interchange','Other','Solar','Thermal','Wind'], # 'Geothermal' has been temp removed 
             'Nicaragua' : ['GEOTHERMAL','HYDRO','INTERCHANGE','SOLAR','THERMAL','WIND']}
    
    def __init__(self,
                 db: str,
                 fltr={},
                 frequency=60*60):
        '''
        Initializes mongoDB cursor

        Parameters
        ----------
        db : str
            Exact name of your MongoDB Database
        col : str, default 'Historic'
            Exact name of the Collection within your MongoDB Database
        fltr : dict, default {}
            Filter object for databse queries. Automatically set to empty which
            behaves the same as SQL SELECT *
        '''
        self.country = db
        self.energy = self.metas[db]
        self.db = self.client[db]
        self.col_hist = self.db['Historic']
        self.col_frcst = self.db['Forecast']
        self.data_hist = None
        self.data_frcst = None
        self.__frequency = frequency
        self.cursor_hist = self.col_hist.find(fltr)
        self.cursor_frcst = self.col_frcst.find(fltr)
        self.error = None

    def get_data(self):
        ''' 
        Grabs all the data from the cursor (cursor needs to be set first, use
        set_cursor(db, col)), then reformats the data into a dataframe with 
        columns corresponding to their respective energy type.

        Return
        --------------
        dataframe of all energy data available in cursor
            * data contains no duplicates
            * data is in consecutive order
            * data contains no missing values within range
        '''
        data = []
        for doc in self.cursor_hist:
            doc.pop('_id')
            for key in doc:
                hour = [np.nan for x in range(len(self.energy) + 1)]
                dt = datetime.strptime(key, '%H-%d/%m/%Y')
                hour[0] = dt
                for item in doc[key]:
                    i = self.energy.index(item['type']) + 1
                    hour[i] = item['value']
                data.append(hour)
        
        # reformat data into dataframe
        data = pd.DataFrame(data, columns = ['ds'] + self.energy)
        # drop duplicates
        data = data.drop_duplicates('ds')
        # resample data to fill missing dates
        data = data.set_index('ds') \
                  .resample('H') \
                  .asfreq() \
                  .reset_index()

        # use only last week
        stop = data.iloc[-1]['ds']
        delta = timedelta(days=7)
        start = stop - delta
        data= data.set_index('ds')
        data = data[start:stop]
        data= data.reset_index()

        print('\n\n*************************')
        print('HISTORIC DATA')
        print('*************************')
        print(data)

        self.data_hist = data
        
        data = []
        for doc in self.cursor_frcst:
            doc.pop('_id')
            for key in doc:
                hour = [np.nan for x in range(len(self.energy) + 1)]
                dt = datetime.strptime(key, '%H-%d/%m/%Y')
                hour[0] = dt
                for item in doc[key]:
                    i = self.energy.index(item['type']) + 1
                    hour[i] = item['value']
                data.append(hour)
        
        # reformat data into dataframe
        data = pd.DataFrame(data, columns = ['ds'] + self.energy)
        # drop duplicates
        data = data.drop_duplicates('ds')
        # resample data to fill missing dates
        data = data.set_index('ds') \
                  .resample('H') \
                  .asfreq() \
                  .reset_index()

        # use same week as forecast
        data= data.set_index('ds')
        data = data[start:stop]
        data= data.reset_index()

        print('\n\n*************************')
        print('FORECAST')
        print('*************************')
        print(data)

        self.data_frcst = data

    def measure_accuracy (self):
        self.error = self.data_hist.set_index('ds') - self.data_frcst.set_index('ds')

        print('\n\n*************************')
        print('ERROR')
        print('*************************')
        print(self.error)

        mae = self.error.abs().mean(axis=0)
        rmse = self.error.apply(np.square).mean(axis=0)
        mape = self.error.div(self.data_hist.set_index('ds'))
        mape = mape.fillna(0) * 100
        mape = mape.abs().mean(axis=0)

        print('\n\n*************************')
        print('MAE')
        print('*************************')
        print(mae)
        print('\n\n*************************')
        print('RMSE')
        print('*************************')
        print(rmse)
        print('\n\n*************************')
        print('MAPE')
        print('*************************')
        print(mape)


def main():
    print('Grabbing data...')
    pm = Performance_Metrics('El_Salvador')
    pm.get_data()
    pm.measure_accuracy()


if __name__ == "__main__":
    main()

