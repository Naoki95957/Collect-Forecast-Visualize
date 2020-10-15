"""
Scrawl data from September 1, 2017 - March 18, 2020.
current data are not saved, writing the data files should be straight forward.
"""
import requests
import datetime
import time
import os
import random
from tqdm import tqdm


class Scraper(object):

    def __init__(self, max_tries=3, max_wait=0.05):
        self.link_template = 'https://npp.gov.in/public-reports/cea/daily/dgr/{}/dgr2-{}.xls'
        self.max_tries = max_tries
        self.max_wait = max_wait
    
    def year_month_day_to_string(self, year, month, date):
        pass

    def generate_all_dates(self, ed_date, st_date=datetime.date(2017, 9, 1)):
        delta = ed_date - st_date
        all_dates = []
        for i in range(delta.days+1):
            tmp_date = st_date + datetime.timedelta(days=i)
            all_dates.append(tmp_date)
        return all_dates

    def get_excel_data(self, url):
        success_flag = False
        for _ in range(self.max_tries):
            resp = requests.get(url)
            if resp.status_code == 200:
                success_flag = True
                break
            else:
                time.sleep(random.uniform(0, self.max_wait))
                # pass
        if success_flag:
            return resp
        else:
            return None
    
    def crawl(self, out_dir, ed_date=datetime.date(2020, 6, 1), st_date=datetime.date(2017, 9, 1)):
        all_dates = self.generate_all_dates(ed_date, st_date)
        all_data = []
        dates_with_data = []
        for tmp_date in tqdm(all_dates[::-1]):
            url = self.template2url(tmp_date)
            data = self.get_excel_data(url)
            if data:
                all_data.append(data)
                dates_with_data.append(tmp_date)
        
        for tmp_date, tmp_data in zip(dates_with_data, all_data):
            self.save(tmp_date, tmp_data, out_dir)

        return all_data, dates_with_data

    def template2url(self, tmp_date):
        # target for 2020, June, 1st --> 'https://npp.gov.in/public-reports/cea/daily/dgr/01-06-2020/dgr2-2020-06-01.xls'
        arg1 = tmp_date.strftime('%d-%m-%Y')
        arg2 = tmp_date.strftime('%Y-%m-%d')
        url = self.link_template.format(arg1, arg2)
        return url
    
    def save(self, tmp_date, data, out_dir):
        fn = 'dgr2-' + tmp_date.strftime('%Y-%m-%d') + '.xls'
        out_dir = os.path.join(out_dir, fn)
        with open(out_dir, 'wb') as fin:
            fin.write(data.content)


if __name__ == '__main__':
    link_template = 'https://npp.gov.in/public-reports/cea/daily/dgr/01-06-2020/dgr2-2020-06-01.xls'
    year = '2020'
    month = '06'
    day = '01'
    scraper = Scraper(max_tries=2, max_wait=0.001)
    all_data, dates_with_data = scraper.crawl('./')
    print()
