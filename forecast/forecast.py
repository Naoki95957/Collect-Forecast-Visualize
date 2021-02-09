import numpy as np
import pandas as pd
import pymongo
import matplotlib.pyplot as plt
from datetime import datetime

# from fbprophet import Prophet
# check prophet version
# print('Prophet %s' % fbprophet.__version__)

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

    def switch_cursor(self, database, collection, filter='{}'):
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
                        print(meta)
                        self.data[meta] = []
                    self.data[meta].append([date, item['value']])

        for meta in self.data:
            self.df[meta] = pd.DataFrame(self.data[meta])
            self.df[meta].columns = ['Datetime', meta]
    
    # TODO: stationarize data (make all statistical properties, such as mean and variance constant)
    def stationarize_data(self):
        pass

    def predict(self):
        pass

    def plot_prediction(self):
        pass


def main():
    print('Preparing data')
    f_es = Forecast('El_Salvador', 'Historic')
    f_es.prep_data()
    for meta in f_es.df:
        f_es.df[meta].plot(x='Datetime')
        plt.show()


if __name__ == "__main__":
    main()
