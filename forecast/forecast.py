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

    def __init__(self):
        self.db = None
        self.col = None
        self.cursor = None
        self.data = {}
        self.model = {}
        self.prediction = {}
        self.periods = 0
        self.first = None

    def set_cursor(self, db, col='Historic', fltr={}):
        '''
        Sets the MongoDB cursor object.

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
        self.db = self.client[db]
        self.col = self.db[col]
        self.cursor = self.col.find(fltr)

    def prep_data(self, years=[datetime.now().year- 1], prtcl='first'):
        ''' 
        Grabs all the data from the cursor (cursor needs to be set first, use
        set_cursor(db, col)), then reformats the data into a dict of
        dataframes with keys corresponding to their respective energy type.

        Parameters
        ----------
        years : list[int], default previous year
            Optional argument to grab data from specific range of years.
        prtcl : {'first', 'last', False}, default 'first'
            Optional argument to define the protocol for removing duplicates.
            For additional information see pandas.DataFrame.drop_duplicates

        Postconditions
        --------------
        * Each encountered energy type will be printed to the console.
        * self.data now contains all of the processed energy data
            * data for each energy type in a separate dataframe
            * data contains no duplicates
            * data is stationary
        '''
        self.data = {}
        self.first = pd.Timestamp(str(years[-1] + 1) + '-01-01T00')

        # grab data from MongoDB
        temp = {}
        for doc in self.cursor:
            doc.pop('_id')
            for key in doc:
                date = datetime.strptime(key, '%H-%d/%m/%Y')
                if date.year not in years:
                    continue
                for item in doc[key]:
                    meta = item['type']
                    if meta not in temp.keys():
                        print(meta)
                        temp[meta] = []
                    temp[meta].append([date, item['value']])

        # reformat data into a list of dataframes
        for meta in temp:
            self.data[meta] = pd.DataFrame(
                temp[meta],
                columns=['Datetime', meta])
            self.data[meta] = self.data[meta].drop_duplicates(
                subset=['Datetime'],
                keep=prtcl)

        # fill missing data
        self.fill_data(years)

    def fill_data(self, years):
        '''
        Fills all dataframes within data to include all possible datetime
        values within given range of years. Also fills any nan value with
        nearest approximation, primarily using ffill().

        Parameters
        ----------
        years: list[int], default previous year
            Inhereted argument from prep_data. Determines expected range of
            datetime entries.

        Postconditions
        --------------
        * data contains entire range of datetime values within years
        * data does not contain any nan values
        '''
        # Expected range
        start = pd.Timestamp(str(years[0]) + '-01-01T00')
        end = pd.Timestamp(str(years[-1]) + '-12-31T23')
        self.periods = 0
        for y in years:
            if self.is_leap_year(y):
                self.periods += 8784
            else:
                self.periods += 8760

        for meta in self.data:
            # check for missing start/end entries
            if start not in self.data[meta]['Datetime'].tolist():
                temp = pd.DataFrame(
                    [[start, np.nan]],
                    columns=['Datetime', meta])
                self.data[meta] = pd.concat([
                    self.data[meta],
                    temp])
            if end not in self.data[meta]['Datetime'].tolist():
                temp = pd.DataFrame(
                    [[end, np.nan]],
                    columns=['Datetime', meta])
                self.data[meta] = pd.concat([
                    self.data[meta],
                    temp])

            # 1) resample data to include all datetimes within given range
            # 2) fill data (redundancy catches all possible exceptions)
            # 3) return data to original format
            self.data[meta] = self.data[meta].set_index('Datetime').resample('H')
            self.data[meta] = self.data[meta].ffill().bfill().fillna(0)
            self.data[meta] = self.data[meta].reset_index()
        
            # validate that df contains full range
            if len(self.data[meta]) != self.periods:
                print('error:', meta, 'of incorrect size')

    def stationarize(self):
        # TODO: make all statistical properties constant
        pass

    def fit(self):
        self.model = {}
        for meta in self.data:
            print("------------------------------")
            print("Fitting", meta)
            print("------------------------------")

            df = self.data[meta].rename(columns={'Datetime': 'ds', meta: 'y'})
            self.model[meta] = Prophet()
            self.model[meta].fit(df)

    def predict(self, per=168):
        for meta in self.model:
            future_dates = self.model[meta].make_future_dataframe(periods=per, freq='h')
            self.prediction[meta] = self.model[meta].predict(future_dates)

    def cross_validation(self):
        pass

    def publish(self):
        for meta in self.prediction:
            forecast = self.prediction[meta][['ds', 'yhat']].iloc[self.periods:]

        start = datetime.date(2020, 1, 1)
        delta = timedelta(days=6)
        # 1/1/2019 to 1/7/2019
        # 1/8/2019 to 1/14/2019
        # 1/15/2019 ...
        for week in range(2):
            end = start + delta
            data = el_salvador.scrape_history(start.year, start.month, start.day, end.year, end.month, end.day)
            id = start.strftime("%d/%m/%Y")
            data['_id'] = id
            db.insert_one(data)
            start = end + datetime.timedelta(days=1)

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
                self.data[meta].plot(x='Datetime')
                plt.show()
        else:
            for meta in self.prediction:
                self.prediction[meta][['ds', 'yhat']].iloc[self.periods:].plot(x='ds')
                plt.show()

    def is_leap_year(self, year):
        if year % 4 == 0:
            if year % 100 != 0:
                return True
            elif year % 100 == 0 and year % 400 == 0:
                return True


def menu():
    print('\nMENU')
    print('----')
    print('c : set cursor')
    print('d : prep data')
    print('f : fit model')
    print('p : make prediction')
    print('ph : plot historical data')
    print('pf : plot forecast data')
    print('cv : print cross validation stats')
    print('db : publish results')
    print('q : quit')


def main():
    model = Forecast()

    action = ''
    while action != 'q':
        menu()
        action = input('>>  ')

        if action == 'c':
            db = input('Database name:  ')
            model.set_cursor(db)
        elif action == 'd':
            n = int(input('Number of years:  '))
            years = []
            for i in range(n):
                years.append(int(input('[' + str(i) + '] >  ')))
            model.prep_data(years)
        elif action == 'f':
            model.fit()
        elif action == 'p':
            model.predict()  
        elif action == 'ph':
            model.plot(hist=True)
        elif action == 'pf':
            model.plot()
        elif action == 'cv':
            pass
        elif action == 'db':
            pass
   

if __name__ == "__main__":
    main()
