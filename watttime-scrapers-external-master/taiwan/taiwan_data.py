import requests
import xmltodict
import pytz
from datetime import datetime, timedelta
import pandas as pd
import logging as log


TZ = pytz.timezone('Asia/Taipei')
BASE_URL = "http://data.taipower.com.tw/opendata/apply/file/d004006/001.xml"
TRANSLATION_DICT = {'電廠': "POWER_PLANT",
                    '機組代號': "UNIT_CODE",
                    '日期時間': "DATE_TIME",
                    'NOX氮氧化物': "NOX",
                    'SO2二氧化硫': "SO2",
                    'OPAC不透光率': "OPAC",
                    'VEL排放流率': "VEL",
                    'TEMP溫度': "TEMP"}


class PolutionData:

    def __init__(self, log):
        self.log = log
        self.rt_demand_ts = None
        self.rt_gen_ts = None

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
            self.log.warning('Failed to get ieso data: {} {} {} '
                             .format(e, code, url))
            return False, 'failure getting generation data', code

        return True, None, text

    def get_realtime_pollution(self, ts=None):
        data = {}
        if ts is None:
            ts = pytz.utc.localize(datetime.utcnow())

        # ts = round_time_down(ts, timedelta(minutes=5)).astimezone(TZ)
        url = BASE_URL
        success, err, xml = self.get_url_data(url)
        print(url)
        if not success:
            self.log.error('failure getting {}, {}'.format(url, err))
            return False, 'could not get data from url', data

        requested_day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        success, err, data = self.parse_rt_pollution(xml, requested_day)

        return success, err, data

    def parse_rt_pollution(self, xml, req_day):
        # data = {}
        raw = xmltodict.parse(xml)
        try:
            # raw_data = \
            #     raw['IMODocument']['IMODocBody']['Generators']['Generator']
            raw_newdataset = raw['NewDataSet']
            raw_data = raw_newdataset['table']
            raw_df = pd.DataFrame(raw_data)
            raw_df = raw_df.rename(TRANSLATION_DICT)
            raw_df.columns = raw_df.columns.map(TRANSLATION_DICT)

            parse_date_lambda = (lambda x: datetime.strptime(x.replace('上午', 'AM').replace('下午', 'PM'), '%Y/%m/%d %p %I:%M:%S'))

            raw_df['DATE_TIME'] = raw_df['DATE_TIME'].apply(parse_date_lambda)
            data = raw_df
        except BaseException as e:
            self.log.info('Could not index realtime generation correctly {}'
                          .format(e))
            return False, 'Could not index generation correctly', None

        return True, None, data


if __name__ == "__main__":
    polutiond = PolutionData(log)
    rt_pollution = polutiond.get_realtime_pollution()

