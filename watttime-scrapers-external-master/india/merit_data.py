import requests
import pytz
from bs4 import BeautifulSoup
from datetime import datetime

TZ = pytz.timezone('Asia/Kolkata')
REAL_TIME_URL = 'http://meritindia.in/Dashboard/BindAllIndiaMap'


def get_real_time_generation(log):
    return MeritData(log).get_real_time_generation()


class MeritData:
    """
    This class is used to pull data from the Government of India's Ministry of
    Power's MERIT dashboard found http://meritindia.in/
    """
    def __init__(self, log):
        self.log = log

    def get_real_time_generation(self):
        """
        Pulls demand, thermal generation, gas generation, hydro generation, and
        renewable generation for the entire country of India
        """
        success, err, raw_html = self.get_url_data(REAL_TIME_URL)
        if success is False:
            return success, err, {}
        return True, None, self.parse_rt_raw_html(
                raw_html=raw_html, query_time=datetime.now(TZ))

    def parse_rt_raw_html(self, raw_html, query_time):
        soup = BeautifulSoup(raw_html, 'html.parser')
        raw_top_lvl_data = soup.findAll('td', {'class': 'rg_Subsection'})
        data = []
        for rdp in raw_top_lvl_data:
            dp_title = rdp.find('div', {'class': 'gen_title_sec'}).text
            dp_value = int(rdp.find(
                'span', {'class': 'counter'}).string.replace(',', ''))
            data.append(self.build_rt_data_point(
                field=dp_title, value=dp_value, query_time=query_time))
        return data

    def build_rt_data_point(self, field, value, query_time):
        data_type = 'demand' if field.lower() == 'demandmet' else 'generation'
        data_dic = {
            'datetime': query_time,
            'data_type': data_type,
            'value': value,
            'region': 'IN'
        }
        if data_type == 'generation':
            data_dic['meta'] = field.split(' ')[0]
        return data_dic

    def get_url_data(self, url):
        code = None
        text = None
        try:
            r = requests.get(url, timeout=300)
            code = r.status_code
            text = r.text
        except requests.exceptions.RequestException as err:
            err_str = 'Failed to get merit data: {} {} {} '.format(
                    err, code, url)
            self.log.warning(err_str)
            return False, err_str, code

        return True, None, text
