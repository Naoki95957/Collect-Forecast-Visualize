"""
    This class retrieves real-time and historical Generation data from all
    El Salvador's power plants by hour. To use this class all you need to do
    is initialize an instance of the class (no parameters ncessaray). Then you
    can simply call scrape_data() to grab all the current generation data for
    the current day. The site reports data by hour, so you can grab up to the
    previous hour. Alternatively if your interested in historical data you can
    use date(year, month, day) to grab data from a certain day or
    date_range(start_year, start_month, start_day, ...) to grab data from a
    range of dates. (see examples in main) The earliest date available on the
    website is 8 Jan 2011.

    Known Bugs:
    -   This class uses selenium webdrivers. If the program doesn't run in
        MAC, open mac_chromedriver86 in drivers folder. If you get a warning:
            “mac_chromedriver86” can’t be opened because the identity of the
            developer cannot be confirmed."
        Go to Apple > System Preferences > Security & Privacy and click the
        'Open Anyway' button. Then rerun program.
    -   The driver.close() or driver.quit() method may result in an error:
            ImportError: sys.meta_path is None, Python is likely shutting down
        This issue has been reported to Python/Selenium.

    Recent website changes:
    -   1 Dec 2020: The site recently added a column for wind (Eólico) which
        will not be present in all historical data

    To update drivers:
    https://selenium-python.readthedocs.io/installation.html

    Last update: 1 Dec 2020
"""

import datetime
import platform
import re
from pathlib import Path
import os
import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class ElSalvador:
    URL = 'http://estadistico.ut.com.sv/OperacionDiaria.aspx'
    driver = None
    TRANSLATION_DICT = {
        'Biomasa': 'Biomass',
        'Geotérmico': 'Geothermal',
        'Hidroeléctrico': 'HydroElectric',
        'Interconexión': 'Interconnection',
        'Eólico': 'Wind',
        'Solar': 'Solar',
        'Térmico': 'Thermal',
        'Eólico': 'Wind'
    }

    def __init__(self):
        options = Options()
        options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            architecture = platform.architecture()[0]
            if architecture == '32bit':
                chrome_driver = '/drivers/linux_chromedriver65_32bit'
            else:
                chrome_driver = '/drivers/linux_chromedriver86_64bit'
            os.chmod(full_path + chrome_driver, 0o777)
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.close()

    def __manual_click(self, element):
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, element)))
        button = self.driver.find_element_by_class_name(element)
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element(button)
        action.click(on_element=button)
        action.perform()
        action.reset_actions()

    def __request_days_back(self, days_back: int):
        """
        Requests n days back on the Daily Operation's page and reloads the
        entire page, so that it can be scraped. Does this by clicking on
        the "dashboard parameters" button and then scrolling down by the
        days back argument, and finally hitting the send button.

        Note: The behavior of the dropdown menu is unpredictable, depending
              on the current date in view. Therefore, this method needs to
              reload the entire page each time.
        """
        self.__manual_click('dx-icon-dashboard-parameters')
        self.__manual_click('dx-dropdowneditor-icon')

        action = selenium.webdriver.ActionChains(self.driver)
        for _ in range(0, days_back + 1):
            action.send_keys(Keys.DOWN)
        action.send_keys(Keys.RETURN)   # select date
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.RETURN)
        action.perform()
        action.reset_actions()

    def __data_point(self, date, value, production_type) -> dict:
        return {'ts': date,
                'value': float(value),
                'ba': 'Unidad de Transacciones',
                'meta': production_type + ' (MWh)'}

    def scrape_data(self) -> list:
        """
        Grabs the daily report for El Salvador.
        Return: list of datapoints
        """
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-word-wrap')))
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-icon-dashboard-parameters')))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        generation_table = soup.find('table', {'class': 'dx-word-wrap'})
        table_headers = generation_table.find('td',
                                              {'class': 'dx-area-column-cell'})
        columns = table_headers.find('table').find_all('span')
        columns = columns[0:-1]
        for i in range(len(columns)):
            columns[i] = columns[i].text

        data_table = generation_table.find('tr', {'class': 'dx-bottom-row'})
        times = data_table.find('td',
                                {'class': 'dx-area-row-cell'}).find_all('span')
        data = data_table.find('td',
                               {'class': 'dx-area-data-cell'}).find('table')
        try:
            scrape_date = times[1].text
        except Exception:
            # this occurs sometime around 10pm PDT
            print("There is no data for this day yet")
            return []
        # this needs to be here since the
        # website reports 1/8/2020 instead of 01/08/2020
        scrape_day = re.search(r'(\d+)/\d+/\d+', scrape_date).group(1)
        scrape_month = re.search(r'\d+/(\d+)/\d+', scrape_date).group(1)
        scrape_year = re.search(r'\d+/\d+/(\d+)', scrape_date).group(1)
        scrape_date = (
            scrape_day.zfill(2) + '/'
            + scrape_month.zfill(2) + '/'
            + scrape_year.zfill(4)
        )
        hours = times[2:-1]
        data_points = []
        for i in range(len(hours)):
            hours[i] = hours[i].text
        entries = data.find_all('tr')
        entries = entries[0:-1]
        for row in range(len(entries)):
            cells = entries[row].find_all('td')
            cells = cells[0:-1]
            for i in range(len(cells)):
                production_type = ElSalvador.TRANSLATION_DICT[columns[i]]
                date = arrow.get(
                    scrape_date + hours[row],
                    'DD/MM/YYYYHH:mm',
                    locale='es',
                    tzinfo='America/El_Salvador').datetime
                value = cells[i].text
                value = value.replace(',', '')
                if not bool(value):
                    value = "0"
                data_points.append(
                    self.__data_point(date, value, production_type))
        return data_points

    def date(self, year, month, day) -> list:
        '''
        Grabs historical for the given date.
        @Param: Date must be a valid date and not in the future.
                Earliest available date is (2011, 1, 8)
        '''
        data = []
        try:
            date = datetime.date(year, month, day)
            today = datetime.date.today()
            days_back = (today - date).days
            self.__request_days_back(days_back)
            data = self.scrape_data()
        except Exception:
            print('Error: Illegal date')
        return data

    def date_range(self, start_year, start_month, start_day,
                   end_year, end_month, end_day) -> list:
        '''
        Grabs historical data within given range (inclusive)
        @Param: Date must be a valid date and not in the future.
                Earliest available date is (2011, 1, 8)
        @Return: data in oldest-newest order
        '''
        data = []
        try:
            start_date = datetime.date(start_year, start_month, start_day)
            end_date = datetime.date(end_year, end_month, end_day)
            delta = datetime.timedelta(days=1)

            while start_date <= end_date:
                data.extend(self.date(
                    start_date.year,
                    start_date.month,
                    start_date.day
                ))
                start_date += delta
        except Exception:
            print('Error: Illegal date(s)')
        return data


if __name__ == "__main__":
    '''
    Example use cases
    '''
    el_salvador = ElSalvador()

    # print("\nLoading today...")
    # today = el_salvador.scrape_data()
    # print("First ten datapoints:")
    # for i in range(10):
    #     print(today[i])

    print("\nLoading date...")
    day = el_salvador.date(2020, 11, 10)
    if len(day) > 0:
        print("First ten datapoints:")
        for i in range(10):
            print(day[i])

    print("\nLoading date range...")
    days = el_salvador.date_range(2020, 11, 8, 2020, 11, 9)
    if len(days) > 0:
        print("First ten datapoints:")
        for i in range(10):
            print(days[i])
        print("Last ten datapoints:")
        for i in range(-10, 0):
            print(days[i])

    # print("\nTrying future date...")
    # future_date = el_salvador.date(2021, 1, 10)
    # print("First ten datapoints:")
    # for i in range(10):
    #     print(future_date[i])

    # print("\nTrying future dates...")
    # future_dates = el_salvador.date_range(2020, 12, 1, 2020, 12, 2)
    # for dp in future_dates:
    #     print(dp)

    # print("\nTrying nonexistant date...")
    # illegal_date = el_salvador.date(2020, 11, 31)

    # print("\nTrying nonexistant dates...")
    # illegal_dates = el_salvador.date_range(20200, 13, 7, 2021, 1, 35)
