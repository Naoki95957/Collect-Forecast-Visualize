from adapters.scraper_adapter import ScraperAdapter
from scrapers.nicaragua import Nicaragua
import datetime
import pandas as pd

'''
The earliest day you can scrape is yesterday.
Data is available in daily chunks by hour
Earliest date is 7/9/2013 (MM/DD/YYYY)
each hour has 53 different values given
Meta types:
'''


class NicaraguaAdapter(ScraperAdapter):

    __frequency = 60 * 60 * 24
    PLANT_DICTIONARY = {
        'AMY1': 'WIND',
        'AMY2': 'WIND',
        'PBP': 'HYDRO',
        'CEN': 'THERMAL',
        'EEC': 'THERMAL',
        'EEC20': 'THERMAL',
        'EGR': 'HYDRO',
        'EOL': 'WIND',
        'PNI1': 'THERMAL',
        'PNI2': 'THERMAL',
        'GSR': 'HYDRO',
        'MTL': 'GEOTHERMAL',
        'HEM': 'HYDRO',
        'HPA1': 'HYDRO',
        'HPA2': 'HYDRO',
        'PHD': 'HYDRO',
        'MTR': 'THERMAL',
        'NSL': 'GEOTHERMAL',
        'PCA1': 'HYDRO',
        'PCA2': 'HYDRO',
        'PCF1': 'HYDRO',
        'PCF2': 'HYDRO',
        'ABR': 'THERMAL',
        'PCG1': 'THERMAL',
        'PCG2': 'THERMAL',
        'PCG3': 'THERMAL',
        'PCG4': 'THERMAL',
        'PCG5': 'THERMAL',
        'PCG6': 'THERMAL',
        'PCG7': 'THERMAL',
        'PCG8': 'THERMAL',
        'PCG9': 'THERMAL',
        'PHC1': 'THERMAL',
        'PHC2': 'THERMAL',
        'PEN3': 'GEOTHERMAL',
        'PEN4': 'GEOTHERMAL',
        'PHL1': 'HYDRO',
        'PHL2': 'HYDRO',
        'PLB1': 'THERMAL',
        'PLB2': 'THERMAL',
        'PMG3': 'THERMAL',
        'PMG4': 'THERMAL',
        'PMG5': 'THERMAL',
        'PMN': 'GEOTHERMAL',
        'PMT1': 'GEOTHERMAL',
        'PMT2': 'GEOTHERMAL',
        'PMT3': 'GEOTHERMAL',
        'PSL': 'SOLAR',
        'TPC': 'THERMAL',
        'LNI-L9040': 'INTERCHANGE',
        'SND-L9090': 'INTERCHANGE',
        'AMY-L9030': 'INTERCHANGE',
        'TCPI-L9150': 'INTERCHANGE'
    }

    historic_data = None
    appended_hist = None
    new_data = None
    appended_new = None
    last_scrape_date = None
    last_scrape_list = []

    def __init__(self):
        self.scraper = Nicaragua()

    def set_last_scraped_date(self, date: datetime.datetime):
        self.last_scrape_list = None
        self.last_scrape_date = date

    def scrape_history(self, start_year, start_month, start_day, end_year, end_month, end_day) -> dict:
        self.historic_data = self.scraper.date_range(start_year, start_month, start_day, end_year, end_month, end_day)

        self.appended_hist = pd.DataFrame(self.historic_data)
        self.appended_hist = self.appended_hist.drop('ba', axis=1)
        self.appended_hist['meta'] = self.appended_hist['meta'].replace(self.PLANT_DICTIONARY)
        self.appended_hist = self.appended_hist.groupby(['ts', 'meta'])['value'].agg('sum').reset_index()

        return self.__filter_data(self.appended_hist)

    def scrape_new_data(self) -> dict:
        will_scrape = False
        if not self.last_scrape_date:
            will_scrape = True
        else:
            delta = datetime.datetime.now() - datetime.timedelta(2) - self.last_scrape_date
            if delta.days > 0:
                will_scrape = True
            if delta.seconds / self.__frequency > 1:
                will_scrape = True

        if will_scrape:
            self.last_scrape_date = datetime.datetime.now() - datetime.timedelta(2)
            year = self.last_scrape_date.year
            month = self.last_scrape_date.month
            day = self.last_scrape_date.day
            self.new_data = self.scraper.date(year, month, day)

            self.appended_new = pd.DataFrame(self.new_data)
            self.appended_new = self.appended_new.drop('ba', axis=1)
            self.appended_new['meta'] = self.appended_new['meta'].replace(self.PLANT_DICTIONARY)
            self.appended_new = self.appended_new.groupby(['ts', 'meta'])['value'].agg('sum').reset_index()

            return self.__filter_data(self.appended_new)

    def __filter_data(self, data) -> dict:

        buffer = dict()
        for i in range(0, len(data) - 1, 6):
            time = data.iat[i, 0].strftime("%H-%d/%m/%Y")
            entries = list()
            for j in range(6):
                dict_val = dict()
                dict_val['value'] = data.iat[i + j, 2]
                dict_val['type'] = data.iat[i + j, 1]
                entries.append(dict_val)

            buffer[time] = entries
        return buffer

    def frequency(self) -> int:
        return self.__frequency


def main():
    na = NicaraguaAdapter()

    start_year = 2020
    start_month = 11
    start_day = 1
    end_year = 2021
    end_month = 1
    end_day = 24

    data = na.scrape_history(start_year, start_month, start_day, end_year, end_month, end_day)
    #data = na.scrape_new_data()
    for each in data:
        print(each, data[each], "\n")


if __name__ == "__main__":
    main()
