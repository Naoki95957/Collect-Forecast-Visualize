from adapters.scraper_adapter import ScraperAdapter
from scrapers.el_salvador import ElSalvador
import copy
import datetime


class ElSalvadorAdapter(ScraperAdapter):

    # in seconds
    __frequency = 60 * 60

    def __init__(self, scraper=ElSalvador):
        super(ElSalvadorAdapter, self).__init__()
        self.scraper = ElSalvador()
        self.last_scrape_date = None
        self.last_scrape_list = []

    def set_last_scraped_date(self):
        '''
        '''
        return None

    def scrape_new_data(self):
        '''
        Should be used in a way to attempt to scrape data by the hour.
        This is used for real-time data logging

        If the last scrape was within an hour, it will return None

        This is based on a differential set in this class and on the
        landing page:
            if the class was set to 6am
            and the landing page says they have data for 8am:
                it should return 7am and 8am entries

        Set this by using 'set_last_scrape_date'

        Returns: dict with data entries.
        '''
        will_scrape = False
        delta = None
        if (not self.last_scrape_date):
            will_scrape = True
        else:
            delta = datetime.datetime.today() - self.last_scrape_date
            if (delta.days > 0):
                will_scrape = True
                self.last_scrape_list = None
            # 60 seconds * 60 minutes
            if (delta.seconds / (self.__frequency) > 1):
                will_scrape = True

        if (will_scrape):
            self.last_scrape_date = datetime.datetime.now()
            data = self.scraper.scrape_data()
            data_copy = copy.deepcopy(self.last_scrape_list)
            self.last_scrape_list = data
            data = self.__filter_data(data)
            data_copy = self.__filter_data(data_copy)
            return {k: data[k] for k in set(data) - set(data_copy)}
        else:
            return None

    def scrape_history(
            self,
            start_year, start_month, start_day,
            end_year, end_month, end_day
            ) -> dict:
        '''
        Returns formated data for the specified range
        '''
        return self.__filter_data(self.scraper.date_range(
            start_year, start_month, start_day,
            end_year, end_month, end_day
        ))

    def __filter_data(self, data: list) -> dict:
        '''
        Removes BA and combines like emissions

        Since El Salvador doesn't have multiple matching emissions,
        this just strips BA and creates a dict:
            keys are time : value is list[dict{value, type}, ...]

        Time is str adjusted to match the format IN THAT TZ: 'HH-DD/MM/YYYY'
        '''
        buffer = dict()
        for i in range(0, len(data)):
            entries = list()
            formatted_time = data[i]['ts'].strftime("%H-%d/%m/%Y")
            if formatted_time in buffer:
                continue
            for j in range(i, len(data)):
                if data[i]['ts'] == data[j]['ts']:
                    dict_val = dict()
                    if data[j]['value'] == 0:
                        continue
                    dict_val['value'] = data[j]['value']
                    dict_val['type'] = data[j]['meta'].replace(" (MWh)", "")
                    entries.append(dict_val)
            buffer[formatted_time] = entries
        return buffer

    def frequency(self):
        '''
        Returns how often this should be scraped: in seconds
        '''
        return self.__frequency
