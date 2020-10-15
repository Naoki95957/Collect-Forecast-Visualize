import requests
import pytz
from datetime import datetime
import logging as log
from bs4 import BeautifulSoup

TZ = pytz.timezone('NZ')
LIVE_DATA_URL = "https://www.transpower.co.nz/power-system-live-data"


class TranspowerData:

    def __init__(self, log):
        self.log = log

    def get_url_data(self, url):
        code = None
        text = None
        try:
            r = requests.get(url, timeout=300)
            code = r.status_code
            text = r.text
            if code != 200:
                raise ValueError('Unsuccessful status code: {}'.format(code))
        except BaseException as e:
            self.log.warning('Failed to get Transpower data: {} {} {} '
                             .format(e, code, url))
            return False, 'failure getting Transpower data', code

        return True, None, text

    def get_parsed_data(self, url, data, parser):
        success, err, text = self.get_url_data(url)
        if not success:
            self.log.error('failure getting {}, {}'.format(url, err))
            return success, err, data

        return parser(text, data)

    def get_load_data(self, data={}):
        return self.get_parsed_data(LIVE_DATA_URL, data, self.parse_load)

    def parse_load(self, text, data):
        try:
            soup = BeautifulSoup(text, features="lxml")
            section = soup.find('div', {'class': 'live-data-summary'})
            time_string = section.find('time').get('datetime')
            ts = datetime.strptime(time_string, '%Y-%m-%d %H:%M')
            entry = {}
            for row in section.find_all('tr'):
                items = row.find_all('td')
                entry[items[0].get_text()] = items[1].get_text()

            data[ts] = entry
        except BaseException as e:
            self.log.info('Failed to parse Transpower data {}'
                          .format(e))
            return False, 'Failed to parse Transpower data', data

        return True, None, data

    def get_generation_data(self, data={}):
        return self.get_parsed_data(LIVE_DATA_URL, data, self.parse_generation)

    def parse_generation(self, text, data):
        try:
            soup = BeautifulSoup(text, features="lxml")
            section = soup.find_all('div', {'class': 'power-generation'})[1] # generation data is in the second table
            time_string = section.find('span', {'class': 'pgen-date'}).get_text()
            if time_string.startswith('(as at) '):
                time_string = time_string[8:]
            ts = datetime.strptime(time_string, '%d %b %Y %H:%M')
            entry = {}
            island = None
            for row in section.find('tbody').find_all('tr'):
                th = row.find('th')
                if th is not None:
                    island = th.get_text()
                    entry[island] = {}
                else:
                    items = row.find_all('td')
                    entry[island][items[0].get_text()] = items[1].get_text()

            data[ts] = entry
        except BaseException as e:
            self.log.info('Failed to parse Transpower data {}'
                          .format(e))
            return False, 'Failed to parse Transpower data', data

        return True, None, data


if __name__ == "__main__":
    scraper = TranspowerData(log)
    load = scraper.get_load_data()
    generation = scraper.get_generation_data()
