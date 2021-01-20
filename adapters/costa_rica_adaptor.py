from adapters import ScraperAdaptor
from scrapers import costa_rica

# documents by day
# {"date": [list of dictionarys (change ts to just hour)]}

# Douments by day
# {(hour, "meta"): value, ...}

# [list of dictionarys]


class CostaRicaAdapter(ScraperAdaptor):
    last_scraped_date = None
    


    def __init__(self, adaptee: costa_rica):
        self.adaptee = adaptee

    def scrape(self, day, month, year):
        # for loop get days, 7 days

        data = self.adaptee.date(year, month, day)
        return data

        # get start, finish data range
        # combine into one week and return

    def frequency(self):
        return
