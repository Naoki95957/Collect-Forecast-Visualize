from adapters import ScraperAdaptor
from scrapers import el_salvador
import datetime


class ElSalvadorAdapter(ScraperAdaptor):

    def __init__(self, scraper: el_salvador):
        self.scraper = el_salvador
        self.last_scrape_date = None

    def scrape(self):
        '''
        Will attempt to scrape data for the week

        If the last scrape was within a week, it will return None

        Returns: dict with data entries for the past week.
        '''
        # for loop get days, 7 days
        will_scrape = False
        delta = (datetime.datetime.today() - self.last_scrape_date)
        if (not self.last_scrape_date or delta.days > 7):
            will_scrape = True

        if (will_scrape):
            # TODO scrape data
            self.last_scrape_date = datetime.datetime.today()
            return dict
        else:
            return None
        # get start, finish data range
        # combine into one week and return

    def frequency(self):
        # shoudn't the adaptor have an integer or date parameter?
        return
