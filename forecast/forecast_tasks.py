from numpy.lib.arraysetops import isin
from forecast.forecast import Forecast
from datetime import datetime, timedelta
import pytz
from enum import Enum
import warnings
import time
import threading

LOCAL_TZ = "America/Los_Angeles"

class ForecasterTypes(Enum):
    '''
    Used to identify what type of forecaster
    '''
    El_Salvador=1,
    Costa_Rica=2,
    Nicaragua=3,
    Mexico=4

class ForecastFactory:

    def get_datetimes(self, offset=timedelta(0), as_tz=None) -> tuple:
        """
        Simple helper function to get start/end datetime objects

        Args:
           offset (timedelta): timedelta value to dial back the time a bit
        Returns:
            tuple: (start, end)
        """
        start = datetime.now(tz=pytz.timezone(LOCAL_TZ))
        end = start + timedelta(days=7)
        start = start - offset
        end = end - offset
        if as_tz:
            start = start.astimezone(pytz.timezone(as_tz))
            end = end.astimezone(pytz.timezone(as_tz))
        return (start, end)

    def el_salvador_forecaster(self) -> Forecast:
        # TODO dial back start/end a few more days/hours, where ever start actually needs to begin
        # for example, if data lags one day:
        # start, end = self.get_datetimes(offset=timedelta(days=1))
        start, end = self.get_datetimes(as_tz='America/El_Salvador')
        return Forecast("El_Salvador", start=start, end=end)

    def costa_rica_forecaster(self) -> Forecast:
        # TODO dial back start/end a few more days/hours
        start, end = self.get_datetimes(as_tz='America/Costa_Rica')
        return Forecast("Costa_Rica", start=start, end=end)

    def nicaragua_forecaster(self) -> Forecast:
        # TODO dial back start/end a few more days/hours
        start, end = self.get_datetimes(as_tz='America/Managua')
        return Forecast("Nicaragua", start=start, end=end)

    def mexico_forecaster(self) -> Forecast:
        """
        NOT IMPLEMENTED
        """
        pass

class ForecasterThread(threading.Thread):
    '''
    Automatically handle tasks for simultanious forecasting

    Make use of multi-threading
    '''
    __kill = False
    __running = False
    bad_forecaster = False
    __bypass = False
    __forecaster_type = None
    __new_forecaster_switcher = {}
    

    # in seconds
    __watchdog_time = 5

    def __init__(self, forecaster: Forecast, upload_data: list):
        super(ForecasterThread, self).__init__()
        if not isinstance(forecaster, Forecast):
            raise TypeError(
                "Expected a Forecast object. Recieved a %s",
                type(forecaster))
        self.forecaster = forecaster
        self.upload_queue = upload_data
        self.__new_forecaster_switcher = {
            ForecasterTypes.Costa_Rica: ForecastFactory.costa_rica_forecaster,
            ForecasterTypes.El_Salvador: ForecastFactory.el_salvador_forecaster,
            ForecasterTypes.Mexico: ForecastFactory.mexico_forecaster,
            ForecasterTypes.Nicaragua: ForecastFactory.nicaragua_forecaster
        }
        if forecaster.db == 'Mexico':
            self.__forecaster_type = ForecasterTypes.Mexico
        elif forecaster.db == 'Nicaragua':
            self.__forecaster_type = ForecasterTypes.Nicaragua
        elif forecaster.db == 'El_Salvador':
            self.__forecaster_type = ForecasterTypes.El_Salvador
        elif forecaster.db == 'Costa_Rica':
            self.__forecaster_type = ForecasterTypes.Costa_Rica
        
    def get_forecaster_failure(self) -> bool:
        '''
        Returns False if forecaster is fine

        Returns True if forecaster failed
        '''
        return self.bad_forecaster

    def reset_forecaster(self):
        '''
        Reset to a new forecaster
        '''
        self.forecaster = self.__new_forecaster_switcher[self.__forecaster_type]()
        self.bad_forecaster = False

    def set_forecaster(self, forecaster: Forecast):
        '''
        Set forecaster to new forecaster
        '''
        self.forecaster = forecaster
        self.bad_forecaster = False

    def set_todays_start_time(self, time: datetime):
        '''
        This will set the reference point for the forecaster landing page
        '''
        if not time.tzinfo:
            raise TypeError("datetime object must be tz aware")
        self.forecaster.start = time

    def schedule_todays_data_now(self):
        '''
        This will let the running thread know to reattempt a scrape now
        '''
        self.__bypass = True

    def attempt_to_queue_data(self):
        '''
        This will attempt to get todays data
        '''
        try:
            data = self.forecaster.get_exported_data()
            if data:
                self.upload_queue.append((self.__forecaster_type, data))
        except Exception as e:
            print(e)
            self.bad_forecaster = True

    def is_alive(self):
        return self.__running

    def start(self):
        self.__kill = False
        return super().start()

    def run(self):
        '''
        Runs the forecaster for realtime data gathering

        Sleeps a majority of its time

        This also has a fake watchdog so that we can kill the process
        in a reasonable amount of time
        '''
        self.__running = True
        freq = self.forecaster.frequency()
        # equals freq so it scrapes once before waiting
        total_sleep = freq
        while not self.__kill:
            if total_sleep < freq and not self.__bypass:
                total_sleep += self.__watchdog_time
                time.sleep(self.__watchdog_time)
            else:
                total_sleep = 0
                self.__bypass = False
                self.attempt_to_queue_data()
        self.__running = False
        return super().run()

    def join(self, timeout=30):
        self.__kill = True
        super().join(timeout)

    def __del__(self):
        self.join()
