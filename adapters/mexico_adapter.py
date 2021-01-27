from adapters.scraper_adapter import ScraperAdapter
from scrapers.mexico import Mexico
import copy
import pytz
import datetime


class MexicoAdapter(ScraperAdapter):

    # in seconds
    __frequency = 60 * 60 * 24 * 7

    def __init__(self, scraper=Mexico):
        self.scraper = Mexico()
        self.last_scrape_date = None
        self.last_scrape_list = []

    def set_last_scraped_date(self, date: datetime.datetime):
        self.last_scrape_list = None
        self.last_scrape_date = date

    def scrape_new_data(self):
        '''
        Should be used in a way to attempt to scrape data by month.
        This is used for 'real-time' data logging:
            at least as close as we can get for now

        If the last scrape was within a month, it will return None

        This is based on a differential set in this class and on the
        landing page

        Set this by using 'set_last_scrape_date'

        Returns: dict with data entries.
        '''
        will_scrape = False
        delta = None
        now = datetime.datetime.now(tz=pytz.timezone("America/Los_Angeles"))
        now = now.astimezone(pytz.timezone('Mexico/General'))
        if (not self.last_scrape_date):
            will_scrape = True
        else:
            delta = now - self.last_scrape_date
            if (delta.days > 0):
                will_scrape = True
                self.last_scrape_list = None
            if (delta.seconds / self.__frequency > 1):
                will_scrape = True

        if (will_scrape):
            data = self.scraper.scrape_month(now.month, now.year)
            data_copy = copy.deepcopy(self.last_scrape_list)
            self.last_scrape_list = data
            data = self.__filter_data(data, start_time=self.last_scrape_date)
            data_copy = self.__filter_data(data_copy)
            self.last_scrape_date = now
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
        return self.__filter_data(self.scraper.scrape_month_range(
            start_month, start_year,
            end_month, end_year
        ))

    def __filter_data(self, data: list, start_time=None) -> dict:
        '''
        Removes BA and combines like emissions

        Since Mexico doesn't have multiple matching emissions,
        this just strips BA and creates a dict:
            keys are time : value is list[dict{value, type}, ...]

        Time is str adjusted to match the format IN THAT TZ: 'HH-DD/MM/YYYY'
        '''
        if not data:
            return dict()
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
        if start_time:
            buffer = self.__filter_time(buffer, start_time)
        return buffer

    def __filter_time(self, data: dict, start_time: datetime) -> dict:
        '''
        Filters out data before and at the start time
        '''
        if not start_time:
            return data
        ordered = sorted(data.keys())
        time_stamp = start_time.strftime("%H-%d/%m/%Y")
        for entry in ordered:
            if entry < time_stamp:
                data.pop(entry)
        return data

    def frequency(self):
        '''
        Returns how often this should be scraped: in seconds
        '''
        return self.__frequency
