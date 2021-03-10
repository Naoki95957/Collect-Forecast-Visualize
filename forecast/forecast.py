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

'''
    Notes
    -----
    * prep_data should allow for a datetime range instead of just years
    * fitting and predicting should allow for specific meta choices
    * Nicaragua's metas are capitalized for some reason
    * Mexico has a few repeated values
        * they always seem to appear at the 0 hour
        * typically first instance is an extreme outlier
            -> should keep last instance instead

    * installing fbprophet: (NOT ALWAYS EASY)
        * MUST look up the documentation
        * depending on your system this will be more or less difficult
        * fbprophet primarily depends on pystan (latest ver 2.19.1.1),
          and a working C++ compiler. I highly suggest setting up a 
          virtual environment to get this up an running:
            1. conda create -n <new_env>
                -> creates new env with name=<new_env>
            2. conda activate <new_env>
                ->activates virtual environment
            3. conda env list
                -> lists env (* next to active env)
            4. install fbprophet by following documentation
            5. conda deactivate
                -> deactivate env (don't forget this line before exiting)
'''

# PYTHON_EXE = "C:\\Users\\Naoki\\anaconda3\\python.exe"
TIMEOUT = 3000

class Forecast:
    '''
    This class can generate predicted values of energy generation data for
    future dates, based on the historical data within the client.
    
    Other key functionalities include:
        * plotting historical and predicted data
        * running statistical accuracy checks
        * publishing predicted data to the client

    Dependencies
    ------------
    * fbprophet (additive regression model for time-series forecasting)
    * pystan 2.19.1.1 (for fbpprophet)
    * properly installed C++ compiler (for fbprophet)
    '''
    client = pymongo.MongoClient(
        "mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/" +
        "WattTime?retryWrites=true&w=majority"
        )
    
    metas = {'El_Salvador' : ['Biomass','Geothermal','HydroElectric','Interconnection','Thermal','Solar','Wind'],
             'Costa_Rica' : ['Hydroelectric','Interchange','Other','Solar','Thermal','Wind','Geothermal'],
             'Nicaragua' : ['GEOTHERMAL','HYDRO','INTERCHANGE','SOLAR','THERMAL','WIND']}
    
    def __init__(self,
                 db: str,
                 col='Historic',
                 fltr={},
                 frequency=60*60,
                 print_statements=False):
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
        self.col = self.db[col]
        self.cursor = self.col.find(fltr)
        self.__frequency = frequency
        self.data = self.__get_data()
        self.model = {}
        self.results = {}
        self.prediction = {}
        self.periods = 168
        self.first = None
        self.print_statements = print_statements

    def __get_data(self):
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
        # grab data from MongoDB
        data = []
        for doc in self.cursor:
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

        # use only last two years to train
        stop = data.iloc[-1]['ds']
        delta = timedelta(days=365 * 2)
        start = stop - delta
        data= data.set_index('ds')
        data = data[start:stop]
        data= data.reset_index()

        return data

    def stationarize(self):
        # TODO: make all statistical properties constant
        pass

    def test_fit(self):
        # test_start = stop + timedelta(hours=1)
        # test_stop = test_start + timedelta(days=6, hours=23)
        # self.test = self.data.loc[test_start:test_stop]
        pass

    def fit(self):
        self.model = {}
        for meta in self.energy:
            if self.print_statements:
                print("------------------------------")
                print("Fitting", meta)
                print("------------------------------")

            df = self.data[['ds', meta]].rename(columns={'ds': 'ds', meta: 'y'})
            self.model[meta] = Prophet()
            self.model[meta].fit(df)

    def predict(self, per=168):
        for meta in self.model:
            if self.print_statements:
                print("------------------------------")
                print("Predicting", meta)
                print("------------------------------")
            future_dates = self.model[meta].make_future_dataframe(periods=per, freq='h')
            self.results[meta] = self.model[meta].predict(future_dates)
            self.prediction[meta] = self.results[meta][['ds', 'yhat']]
            self.prediction[meta] = self.prediction[meta].iloc[-per:]

    def get_exported_data(self, worker=False) -> list:
        """
        Generates a dictionary of values in the DB form for upload

        Does not need to check for entries, only needs to hand off data

        Yes this looks gnarly and that's because list compresion is faster in df
        than iteration of rows

        Args:
            worker (boolean): indicated whether or not it needs to get a worker to get the data

        Returns:
            list: in DB format
        """
        class_path = os.getcwd()
        if not class_path.endswith('forecast'):
            class_path = os.path.join(class_path, 'forecast')
        file_path = copy.deepcopy(class_path)
        file_path = os.path.join(file_path, self.country + 'prediciton')
        class_path = os.path.join(class_path, 'forecast.py')
        if worker:
            command = [sys.executable, class_path, self.country, file_path]
            if self.print_statements:
                print(command)
            subprocess.Popen(command)
            count = 0
            while not os.path.isfile(file_path):
                count += 1
                if count > TIMEOUT:
                    raise TimeoutError("Process failed to complete in time:", TIMEOUT, "s")
                time.sleep(1)
        self.prediction = pickle.load(open(file_path, 'rb'))
        os.remove(file_path)
        meta_types = self.metas[self.country]
        full_frame = copy.deepcopy(meta_types)
        full_frame.extend(['ds'])
        # format 
        # TODO: make cleaner
        pred = self.prediction[full_frame[0]]
        pred = pred.rename(columns = {'ds':'ds', 'yhat':full_frame[0]})
        for meta in self.prediction:
            if(meta not in pred.columns):
                pred[meta] = self.prediction[meta]['yhat']
        if self.print_statements:
            print(pred)
        output = {}
        for row in pred.index:
            output.update(
                self.__format_helper(
                    pred['ds'][row],
                    [
                        (meta, pred[meta][row])
                        for meta in meta_types
                    ]
                )
            )
        return output

    def __format_helper(self, hour: datetime, values: list) -> dict:
        """
        Simple function that helps format data since it's a little complicated to make out of a lambda

        This does the bulk of the formatting work and does so for one entry

        Args:
            hour (datetime): the DS value
            values (list): the rest of the columns values in tuple form (type, value)

        Returns:
            dict: Single entry in the DB format
        """ 
        return {
            hour.strftime("%H-%d/%m/%Y"):[
                {'value': val[1], 'type': val[0]}
                for val in values
            ]
        }


    def frequency(self) -> int:
        """
        Gets the frequency at which this class should make predictions

        Returns:
            int: time in seconds to sleep before next iteration
        """
        return self.__frequency
    
    def plot(self, hist=False):
        '''
        Creates a simple plot, using matplotlib.pyplot, for each dataframe
        within given dataset. To quit you must exit out of each successive
        plot (plots can also be saved).

        TODO: Add more potential arguments and plot types

        Parameters
        ----------
        hist : bool, default False
            If set to True, uses historical data for plots. Otherwise, it
            will default to plotting the predicted data.
        '''
        if hist:
            for meta in self.data:
                self.data[meta].plot()
                plt.show()
        else:
            for meta in self.prediction:
                print(meta)
                print('E')
                print(self.prediction[meta])
                ax = self.prediction[meta].plot()
                print('A')
                print(self.test[meta])
                self.test[meta].plot(ax=ax, title=meta, )
                plt.show()

    def get_prediction(self):
        return

    def is_leap_year(self, year):
        if year % 4 == 0:
            if year % 100 != 0:
                return True
            elif year % 100 == 0 and year % 400 == 0:
                return True

def main():
    if len(sys.argv) > 1:
        try:
            print('Grabbing', sys.argv[1])
            model = Forecast(sys.argv[1])
            model.fit()
            model.predict()
            pickle.dump(model.prediction, open(sys.argv[2], 'wb'))
            print('successfully dumped prediction')
        except Exception as e:
            print(e)
    else:
        print('Grabbing', 'El_Salvador')
        model = Forecast('El_Salvador', print_statements=True)
        model.fit()
        model.predict()
        model.plot()


if __name__ == "__main__":
    main()
