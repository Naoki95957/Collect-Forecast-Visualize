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

    def __init__(self, db, col='Historic', fltr={}):
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
        self.data = self.__get_data()
        self.model = {}
        self.prediction = {}
        self.periods = 0
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
                  .reset_index()
        
        return data

    def add_fourier_terms(df, year_k, week_k, day_k):
        """
        df: dataframe to add the fourier terms to 
        year_k: the number of Fourier terms the year period should have. Thus the model will be fit on 2*year_k terms (1 term for 
                sine and 1 for cosine)
        week_k: same as year_k but for weekly periods
        day_k:  same as year_k but for daily periods
        """
        
        for k in range(1, year_k+1):
            # year has a period of 365.25 including the leap year
            df['year_sin'+str(k)] = np.sin(2 *k* np.pi * df.index.dayofyear/365.25) 
            df['year_cos'+str(k)] = np.cos(2 *k* np.pi * df.index.dayofyear/365.25)

        for k in range(1, week_k+1):
            
            # week has a period of 7
            df['week_sin'+str(k)] = np.sin(2 *k* np.pi * df.index.dayofweek/7)
            df['week_cos'+str(k)] = np.cos(2 *k* np.pi * df.index.dayofweek/7)


        for k in range(1, day_k+1):
            
            # day has period of 24
            df['hour_sin'+str(k)] = np.sin(2 *k* np.pi * df.index.hour/24)
            df['hour_cos'+str(k)] = np.cos(2 *k* np.pi * df.index.hour/24) 

    def train_test(data, test_size = 168, scale = False, cols_to_transform=None, include_test_scale=False):
        """
        
            Perform train-test split with respect to time series structure
            
            - df: dataframe with variables X_n to train on and the dependent output y which is the column 'SDGE' in this notebook
            - test_size: size of test set
            - scale: if True, then the columns in the -'cols_to_transform'- list will be scaled using StandardScaler
            - include_test_scale: If True, the StandardScaler fits the data on the training as well as the test set; if False, then
            the StandardScaler fits only on the training set.
            
        """
        df = data.copy()
        # get the index after which test set starts
        # test_index = int(len(df)*(1-test_size))
        test_index = len(df) - test_size
        
        # StandardScaler fit on the entire dataset
        if scale and include_test_scale:
            scaler = StandardScaler()
            df[cols_to_transform] = scaler.fit_transform(df[cols_to_transform])
            
        X_train = df.drop('Solar', axis = 1).iloc[:test_index]
        y_train = df.Solar.iloc[:test_index]
        X_test = df.drop('Solar', axis = 1).iloc[test_index:]
        y_test = df.Solar.iloc[test_index:]
        
        # StandardScaler fit only on the training set
        if scale and not include_test_scale:
            scaler = StandardScaler()
            X_train[cols_to_transform] = scaler.fit_transform(X_train[cols_to_transform])
            X_test[cols_to_transform] = scaler.transform(X_test[cols_to_transform])
        
        return X_train, X_test, y_train, y_test

    def fit_sarimax(self, start, end, meta, prtcl='zfill', exog=None, p=2, d=1, q=1, P=1, D=0, Q=1, m=24):
        self.model[meta] = None
        print("------------------------------")
        print("Fitting", meta)
        print("------------------------------")

        # format data
        df = self.data[[meta]]
        if prtcl == 'zfill':
            df = df.fillna(0)
        if exog:
            df['Altitude'] = df['ds'].apply(exog)
        df = df.set_index('ds')
        df = df.loc[start:end]

        # Creating the lag variables
        for i in range(24):
            df['lag'+str(i+1)] = df[meta].shift(i+1)
        lag = df.dropna()
        add_fourier_terms(lag, year_k=5, week_k=5 , day_k=5)

        # Choosing a subset of the above dataframe; removing the lags and the hour bins
        cyc = lag.drop([col for col in lag if col.startswith('lag')], axis=1)

        # Creating the training and test datasets
        # sdgecyc is the dataframe with fourier series variables for hour, week and year
        if exog:
            cols_to_transform = ['Altitude']
        else:
            cols_to_transform = None

        X_train = lag.drop(meta, axis = 1)
        y_train = lag[[meta]]

        # Since ARIMA model uses the past lag y values, scaling the energy values as well. 
        #i.e. fit the scaler on y_train and transform it and also transform y_test using the same scaler if required later

        scaler1 = StandardScaler()
        y_train = pd.DataFrame(scaler1.fit_transform(y_train.values.reshape(-1,1)),
                               index = y_train.index,
                               columns = [meta])

        self.model[meta] = SARIMAX(y_train, order=(p,d,q), seasonal_order=(P, D, Q, m), trend='c')
        results = model_opt.fit()
        # plotting the residuals and checking if they meet the i.i.d (independent and identically distributed) requirements
        _ = results.plot_diagnostics(figsize=(12, 7))

        # Predictions on train set. Predicting only the last week of the training set

        # Setting dynamic = True so that the model won't use actual enegy values for prediction. Basically the model will use
        # the lag terms and moving average terms of the already forecasted energy values. So, we will see the errors 
        #(confidence interval) increasing with each forecast.
        pred = results.get_prediction(start=X_train_lag.index[-24*7], end=X_train_lag.index[-1], dynamic=True)
        pred_ci = pred.conf_int()

        pred1 = scaler1.inverse_transform(pred.predicted_mean)
        pred_ci1 = scaler1.inverse_transform(pred.conf_int())

        y_actual_train = np.squeeze(scaler1.inverse_transform(y_train_lag))
        y_actual_train = pd.Series(y_actual_train, index = X_train_lag.index )

        pred1 = pd.Series(pred1, index = X_train_lag.iloc[-24*7:, :].index )
        pred_ci1 = pd.DataFrame(pred_ci1, index = pred1.index, columns = ['lower he', 'upper he'])

        lower_limits = pred_ci1.loc[:,'lower he']
        upper_limits = pred_ci1.loc[:,'upper he']

        pred = results.get_forecast(steps = 24*7)
        pred_ci = pred.conf_int()

        pred2 = scaler1.inverse_transform(pred.predicted_mean)
        pred_ci2 = scaler1.inverse_transform(pred.conf_int())

        y_actual = y_test_lag.iloc[:24*7]

        pred2 = pd.Series(pred2, index = X_test_lag.iloc[:24*7, :].index )
        pred_ci2 = pd.DataFrame(pred_ci2, index = pred2.index, columns = ['lower he', 'upper he'])

        lower_limits = pred_ci2.loc[:,'lower he']
        upper_limits = pred_ci2.loc[:,'upper he']

        # plot the predictions
        plt.figure(figsize = (15,7))
        _ = plt.plot(y_actual.index, y_actual, label='observed')

        # plot your mean predictions
        _ = plt.plot(pred2.index, pred2.values, color='r', label='forecast')

        # shade the area between your confidence limits
        _ = plt.fill_between(lower_limits.index, lower_limits, upper_limits, color='pink')

        # set labels, legends and show plot
        _ = plt.xlabel('Date')
        _ = plt.ylabel('Energy consumption GWH')
        _ = plt.legend()
        _ = plt.title('Testing the SARIMAX (2,1,1)x(1,0,0,24) model on the testing set: predicting the 1st week')
        
    def predict(self, per=168):
        for meta in self.model:
            future_dates = self.model[meta].make_future_dataframe(periods=per, freq='h')
            self.prediction[meta] = self.model[meta].predict(future_dates)

    def stationarize(self):
        # TODO: make all statistical properties constant
        pass

    def cross_validation(self):
        pass

    def publish(self, db, col):
        forecast = pd.DataFrame()
        for meta in self.prediction:
            temp = self.prediction[meta][['ds', 'yhat']].iloc[self.periods:]
            forecast = pd.concat(forecast, temp)
        print(forecast)

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
                self.data[[meta]].plot()
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
            model.publish()


if __name__ == "__main__":
    main()
