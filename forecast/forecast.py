import numpy as np
import pandas as pd
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from fbprophet import Prophet

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
                 db,
                 col='Historic',
                 fltr={},
                 start=datetime(2020,1,1,0),
                 stop=datetime(2020,12,31,23),
                 test=True):
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
        self.start = start
        self.stop = stop
        self.data = self.__get_data()
        self.train = self.data.loc[start:stop]
        if test:
            test_start = stop + timedelta(hours=1)
            test_stop = test_start + timedelta(days=6, hours=23)
            self.test = self.data.loc[test_start:test_stop]
        else:
            self.test = None
        self.model = {}
        self.results = {}
        self.prediction = {}
        self.periods = 168
        self.first = None

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
        data= data.set_index('ds') \
                  .resample('H') \
                  .asfreq() \
        
        return data

    def stationarize(self):
        # TODO: make all statistical properties constant
        pass

    def fit(self):
        self.model = {}
        for meta in self.energy:
            print("------------------------------")
            print("Fitting", meta)
            print("------------------------------")

            df = self.train.reset_index()
            df = df[['ds', meta]].rename(columns={'ds': 'ds', meta: 'y'})
            self.model[meta] = Prophet()
            self.model[meta].fit(df)

    def predict(self, per=168):
        for meta in self.model:
            print("------------------------------")
            print("Predicting", meta)
            print("------------------------------")
            future_dates = self.model[meta].make_future_dataframe(periods=per, freq='h')
            self.results[meta] = self.model[meta].predict(future_dates)
            self.prediction[meta] = self.results[meta][['ds', 'yhat']]
            self.prediction[meta] = self.prediction[meta].iloc[-per:]
            self.prediction[meta] = self.prediction[meta].set_index('ds')

    def cross_validation(self):a
        pass

    def publish(self):
        # for meta in self.prediction:
        #     forecast = self.prediction[meta][['ds', 'yhat']].iloc[self.periods:]

        # start = datetime.date(2020, 1, 1)
        # delta = timedelta(days=6)
        # # 1/1/2019 to 1/7/2019
        # # 1/8/2019 to 1/14/2019
        # # 1/15/2019 ...
        # for week in range(2):
        #     end = start + delta
        #     data = el_salvador.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
        #     id = start.strftime("%d/%m/%Y")
        #     data['_id'] = id
        #     db.insert_one(data)
        #     start = end + datetime.timedelta(days=1)
        pass

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
    print('Grabbing El_Salvador')
    model = Forecast('El_Salvador')
    model.fit()
    model.predict()
    model.plot()

if __name__ == "__main__":
    main()
