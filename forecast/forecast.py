import numpy as np
import pandas as pd
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime
# from fbprophet import Prophet

'''
    Notes:
        prep_data should allow for a datetime range instead of just years
        Nicaragua's metas are capitalized for some reason
        Mexico has a few repeated values
            * they always seem to appear at the 0 hour
            * typically first instance is an extreme outlier
              -> should keep last instance instead
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
    fbprophet : additive regrssion model for time-series forecasting
    pystan 2.19.1.1 (for fbpprophet)
    properly installed C++ compiler (for fbprophet)
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
        # self.model = Prophet()
        self.prediction = None

    def set_cursor(self, db, col, fltr={}):
        '''
        Sets the MongoDB cursor object.

        Parameters
        ----------
        db : str
            Exact name of your MongoDB Database
        col : str
            Exact name of the Collection within your MongoDB Database
        fltr : dict
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

        Example
        -------
        >>> model.prep_data(years=[2019,2020])
        Biomass
        Geothermal
        Hydroelectric
        Interconnection
        Thermal
        Solar
        Wind
        '''
        self.data = {}

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
        periods = 0
        for y in years:
            if self.is_leap_year(y):
                periods += 8784
            else:
                periods += 8760

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
            if len(self.data[meta]) != periods:
                print('error:', meta, 'of incorrect size')

    def is_leap_year(self, year):
        if year % 4 == 0:
            if year % 100 != 0:
                return True
            elif year % 100 == 0 and year % 400 == 0:
                return True

    def plot_data(self):
        '''
        Create a simple plot, using matplotlib.pyplot, for each dataframe within
        data. Uses the datetime values as the x axis. To quite you must exit out 
        of each successive plot (plots can also be saved).
        '''
        for meta in self.data:
            self.data[meta].plot(x='Datetime')
            plt.show()
    
    def stationarize_data(self):
        # TODO: make all statistical properties constant
        pass

    def predict(self):
        pass

    def plot_prediction(self):
        pass


def main():
    model = Forecast()

    print('Preparing data for El Salvador:')
    print('Energy types found:\n')
    model.set_cursor('El_Salvador', 'Historic')
    model.prep_data()
    show_plot = input('\nWould you like to see plots (y/n): ')
    if show_plot == 'y':
        model.plot_data()

    print('Preparing data for Mexico:')
    print('Energy types found:\n')
    model.set_cursor('Mexico', 'Historic')
    model.prep_data(prtcl='last')
    show_plot = input('\nWould you like to see plots (y/n): ')
    if show_plot == 'y':
        model.plot_data()

    print('Preparing data for Nicaragua:')
    print('Energy types found:\n')
    model.set_cursor('Nicaragua', 'Historic')
    model.prep_data()
    show_plot = input('\nWould you like to see plots (y/n): ')
    if show_plot == 'y':
        model.plot_data()

    print('Preparing data for Costa Rica:')
    print('Energy types found:\n')
    model.set_cursor('Costa_Rica', 'Historic')
    model.prep_data()
    show_plot = input('\nWould you like to see plots (y/n): ')
    if show_plot == 'y':
        model.plot_data()
    

if __name__ == "__main__":
    main()
