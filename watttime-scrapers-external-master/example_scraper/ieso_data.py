import requests
import xmltodict
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from time import sleep

from dateutil.parser import parse
from ..common.common import merge, round_time_down

TZ = pytz.timezone('EST')
HIST_GEN_URL = ('http://reports.ieso.ca/public/GenOutputbyFuelHourly/'
                'PUB_GenOutputbyFuelHourly_{}.xml')  # insert year 2019
HIST_DEMAND_URL = 'http://reports.ieso.ca/public/Demand/PUB_Demand_{}.csv'
RT_DEMAND_URL = ('http://reports.ieso.ca/public/RealtimeConstTotals/'
                 'PUB_RealtimeConstTotals_{}{}.xml')  # 2019041201
RT_DEMAND_TIME_FORMAT = '%Y%m%d'

RT_GENERATION_URL = ('http://reports.ieso.ca/public/GenOutputCapability/'
                     'PUB_GenOutputCapability_{}.xml')
RT_GENERATION_TIME_FORMAT = '%Y%m%d'


class IesoData:
    def __init__(self, log):
        self.log = log
        self.rt_demand_ts = None
        self.rt_gen_ts = None

    def get_historical_demand(self, start, end):
        data = {}
        start = round_time_down(start, timedelta(minutes=5))
        _start = start
        while start <= end:
            url = HIST_DEMAND_URL.format(start.year)
            start += relativedelta(years=1)
            success, err, csv = self.get_url_data(url)
            if not success:
                self.log.error('failure getting {}, {}'.format(url, err))
                continue
            year_data = self.parse_historical_demand(csv)
            data = merge(data, year_data, log=self.log)

        times = list(data.keys())
        times.sort()
        if times:
            request_start = times[-1] + timedelta(minutes=5)
        else:
            request_start = _start
        # Pull from recent data endpoint if more recent data is requested
        while request_start < end:
            success, err, rt_data = self.get_realtime_demand(request_start)
            if success:
                data = merge(rt_data, data, log=self.log)
            request_start += timedelta(hours=1)

        return True, None, data

    def parse_historical_demand(self, raw_csv):
        data = {}
        csv_rows = raw_csv.splitlines()[4:]
        for row in csv_rows:
            cols = row.split(',')
            if len(cols) < 4:
                continue
            try:
                ts = parse(cols[0]) + timedelta(hours=(int(cols[1])-1))
                ts = TZ.localize(ts)
                demand = float(cols[3])
            except BaseException as e:
                self.log.error('error parsing demand row: {}, {}'
                               .format(e, row))
                continue
            data[ts] = demand
        return data

    def get_historical_generation(self, start, end):
        data = {}
        _start = start
        while start <= end:
            url = HIST_GEN_URL.format(start.year)
            start += relativedelta(years=1)
            success, err, csv = self.get_url_data(url)
            if not success:
                self.log.error('failure getting {}, {}'.format(url, err))
                continue
            year_data = self.parse_historical_generation(csv)
            data = merge(data, year_data, log=self.log)

        times = list(data.keys())
        times.sort()
        if times:
            request_start = times[-1] + timedelta(minutes=5)
        else:
            request_start = _start
        # Pull from recent data endpoint if more recent data is requested
        while request_start < end:
            success, err, rt_data = self.get_realtime_generation(request_start)
            if success:
                data = merge(rt_data, data, log=self.log)
            request_start += relativedelta(days=1)

        return True, None, data

    def parse_historical_generation(self, raw_xml):
        raw_dict = xmltodict.parse(raw_xml)
        data = {}
        try:
            daily_data = raw_dict['Document']['DocBody']['DailyData']
            if type(daily_data) != list:
                raise Exception('type daily data {}'.format(type(daily_data)))
        except BaseException as e:
            self.log.error('Error parsing historical gen: {}'.format(e))

        for day_data in daily_data:
            try:
                day = TZ.localize(parse(day_data['Day']))
                day_hour_data = day_data['HourlyData']
            except BaseException as e:
                self.log.error('error parsing day data {}'.format(e))
                continue
            for hourly_data in day_hour_data:
                try:
                    hour = int(hourly_data['Hour']) - 1
                    success, wind, hydro = self.parse_hourly_gen(hourly_data)
                    if not success:
                        continue
                    ts = day + timedelta(hours=hour)
                    data[ts] = wind + hydro
                except BaseException as e:
                    self.log.error('error in hourly data {}'.format(e))
                    continue

        return data

    def parse_hourly_gen(self, hourly_data):
        hydro = None
        wind = None
        for fuel_data in hourly_data['FuelTotal']:
            try:
                if fuel_data['Fuel'] == 'HYDRO':
                    hydro = float(fuel_data['EnergyValue']['Output'])
                if fuel_data['Fuel'] == 'WIND':
                    wind = float(fuel_data['EnergyValue']['Output'])
            except BaseException as e:
                self.log.error('error parsing hourly data {}'.format(e))
                continue
        if None in [hydro, wind]:
            self.log.error('Missing wind or hydro: {}, {}'.format(hydro, wind))
            return False, wind, hydro

        return True, wind, hydro

    def get_realtime_demand(self, ts=None, ntries=0):
        if ntries > 600:
            return False, 'number of tries exceeded', {}

        data = {}
        is_realtime_request = False
        if ts is None:
            is_realtime_request = True
            ts = pytz.utc.localize(datetime.utcnow()).astimezone(TZ)

        ts = round_time_down(ts, timedelta(minutes=5))
        hour_str = str(ts.hour+1)
        if len(hour_str) == 1:
            hour_str = '0' + hour_str

        url = RT_DEMAND_URL.format(ts.strftime(RT_DEMAND_TIME_FORMAT),
                                   hour_str)
        success, err, xml = self.get_url_data(url)
        if not success:
            if is_realtime_request or ntries > 0 and xml == 404:
                self.log.info('ieso realtime: data not available {}'
                              .format(ts.isoformat()))
                sleep(10)
                return self.get_realtime_demand(ts, ntries+1)

            self.log.error('failure getting {}, {}'.format(url, err))
            return False, 'could not get data from url', data

        requested_time = round_time_down(ts, timedelta(hours=1))
        success, err, data = self.parse_rt_demand(xml, requested_time)
        if not success:
            return success, err, data

        if is_realtime_request or ntries > 0:
            if ts not in data:
                self.log.info('ieso realtime: data not available {}'
                              .format(ts.isoformat()))
                sleep(10)
                return self.get_realtime_demand(ts, ntries+1)

        return success, err, data

    def parse_rt_demand(self, xml, requested_time):
        data = {}
        raw = xmltodict.parse(xml)
        try:
            raw_data = raw['Document']['DocBody']['Energies']['IntervalEnergy']
        except BaseException as e:
            self.log.info('Could not index realtime demand correctly {}'
                          .format(e))
            return False, 'Could not index demand correctly', None

        # Different format when the hour begins.
        if type(raw_data) != list:
            try:
                raw_data = [raw_data]
            except BaseException:
                self.log.error('raw data: {}'.format(raw_data))
                raise ValueError('ieso error parsing')

        for interval_data in raw_data:
            try:
                interval = int(interval_data['Interval']) - 1
                market_data_list = interval_data['MQ']
                for market_data in market_data_list:
                    if market_data['MarketQuantity'] == 'ONTARIO DEMAND':
                        value = float(market_data['EnergyMW'])
                        ts = requested_time + timedelta(minutes=interval*5)
                        data[ts] = value
            except BaseException:
                self.log.warning('exception parsing realtime demand',
                                 exc_info=True)
                self.log.info('interval_data is: {}'.format(interval_data))
                self.log.info('raw_data is: {}'
                              .format(raw['Document']['DocBody']['Energies']))
                continue

        return True, None, data

    def get_realtime_generation(self, ts=None):
        data = {}
        if ts is None:
            ts = pytz.utc.localize(datetime.utcnow())

        ts = round_time_down(ts, timedelta(minutes=5)).astimezone(TZ)
        url = RT_GENERATION_URL.format(ts.strftime(RT_GENERATION_TIME_FORMAT))
        success, err, xml = self.get_url_data(url)
        print(url)
        if not success:
            self.log.error('failure getting {}, {}'.format(url, err))
            return False, 'could not get data from url', data

        requested_day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        success, err, data = self.parse_rt_generation(xml, requested_day)

        return success, err, data

    def parse_rt_generation(self, xml, req_day):
        data = {}
        raw = xmltodict.parse(xml)
        try:
            raw_data = \
                raw['IMODocument']['IMODocBody']['Generators']['Generator']
        except BaseException as e:
            self.log.info('Could not index realtime generation correctly {}'
                          .format(e))
            return False, 'Could not index generation correctly', None

        for generator in raw_data:
            try:
                if generator['FuelType'] in ['WIND', 'HYDRO']:
                    outputs = generator['Outputs']['Output']
                    for hourly_data in outputs:
                        try:
                            gen = float(hourly_data['EnergyMW'])
                            hour = int(hourly_data['Hour']) - 1
                        except BaseException as e:
                            self.log.error('Error in rt gen: {}. raw: {}'
                                           .format(e, hourly_data))
                            continue
                        ts = req_day + timedelta(hours=hour)
                        if ts not in data:
                            data[ts] = 0
                        data[ts] += gen
            except BaseException as e:
                self.log.error('exception parsing rt gen {}'.format(e))
                continue

        return True, None, data

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
