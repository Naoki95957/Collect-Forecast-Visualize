import numpy as np
import pandas as pd
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime
# from fbprophet import Prophet

class Forecast:
    client = pymongo.MongoClient("mongodb+srv://BCWATT:WattTime2021@cluster0.tbh2o.mongodb.net/WattTime?retryWrites=true&w=majority")

    def __init__(self, database, collection, filter={}):
        self.db = self.client[database]
        self.coll = self.db[collection]
        self.cursor = self.coll.find(filter)
        self.data = {}
        self.df = {}
        # self.model = Prophet()
        self.prediction = None

    def switch_cursor(self, database, collection, filter={}):
        self.db = client[database]
        self.coll = db[collection]
        self.cursor = collection.find(filter)

    def prep_data(self, years=[2020]):
        for doc in self.cursor:
            doc.pop('_id')
            for key in doc:
                date = datetime.strptime(key, '%H-%d/%m/%Y')
                if date.year not in years:
                    continue
                for item in doc[key]:
                    meta = item['type']
                    if meta not in self.data.keys():
                        print('\t', meta)
                        self.data[meta] = []
                    self.data[meta].append([date, item['value']])

        for meta in self.data:
            self.df[meta] = pd.DataFrame(self.data[meta])
            self.df[meta].columns = ['Datetime', meta]
    
    def plot_data(self):
        for meta in self.df:
            self.df[meta].plot(x='Datetime')
            plt.show()
    
    # TODO: stationarize data (make all statistical properties, such as mean and variance constant)
    def stationarize_data(self):
        pass

    def predict(self):
        pass

    def plot_prediction(self):
        pass


def main():
    print('Preparing data for El Salvador:')
    print('Energy types found:')
    f_es = Forecast('El_Salvador', 'Historic')
    f_es.prep_data()
    show_plot = input('Would you like to see plots (y/n): ')
    if show_plot == 'y':
        f_es.plot_data()

    print('Preparing data for Mexico:')
    print('Energy types found:')
    f_mex = Forecast('Mexico', 'Historic')
    f_mex.prep_data()
    show_plot = input('Would you like to see plots (y/n): ')
    if show_plot == 'y':
        f_mex.plot_data()

    print('Preparing data for Nicaragua:')
    print('Energy types found:')
    f_mex = Forecast('Nicaragua', 'Historic')
    f_mex.prep_data()
    show_plot = input('Would you like to see plots (y/n): ')
    if show_plot == 'y':
        f_mex.plot_data()

    print('Preparing data for Costa Rica:')
    print('Energy types found:')
    f_mex = Forecast('Costa_Rica', 'Historic')
    f_mex.prep_data()
    show_plot = input('Would you like to see plots (y/n): ')
    if show_plot == 'y':
        f_mex.plot_data()
    

if __name__ == "__main__":
    main()
