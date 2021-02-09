import numpy as np
import pandas as pd
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime
# from fbprophet import Prophet

class Forecast:
    client = pymongo.MongoClient(
        "mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/" +
        "WattTime?retryWrites=true&w=majority"
        )

    def __init__(self):
        self.db = None
        self.col = None
        self.cursor = None
        self.data = {}
        self.df = {}
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

    def prep_data(self, years=[2020]):
        ''' 
        Grabs all the data from the cursor (cursor needs to be set first, use 
        set_cursor(db, col)), then reformats the data into a dict of arrays 
        (nested lists of size [n, 2]) mapped to their respective energy type. 
        Finally, uses the data to create a dict of dataframes for each energy
        type and stores them in df.

        Prints all the energy types found to the console.

        Parameters
        ----------
        years : list[int]
            Optional argument to grab data from specific years. Automatically
            set to grab data from previous year.

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
        self.df = {}

        for doc in self.cursor:
            doc.pop('_id')
            for key in doc:
                date = datetime.strptime(key, '%H-%d/%m/%Y')
                if date.year not in years:
                    continue
                for item in doc[key]:
                    meta = item['type']
                    if meta not in self.data.keys():
                        print(meta)
                        self.data[meta] = []
                    self.data[meta].append([date, item['value']])

        for meta in self.data:
            self.df[meta] = pd.DataFrame(self.data[meta])
            self.df[meta].columns = ['Datetime', meta]
    
    def plot_data(self):
        '''
        Creates a simple plot, using matplotlib.pyplot, for each datafram within
        df. Uses the datetime values as the x axis. To quite you must exit out 
        of each successive plot. Plots can also be saved.
        '''
        for meta in self.df:
            self.df[meta].plot(x='Datetime')
            plt.show()
    
    # TODO: make all statistical properties constant
    def stationarize_data(self):
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
    model.prep_data()
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
