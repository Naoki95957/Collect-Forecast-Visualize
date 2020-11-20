import datetime
import platform
import re
from datetime import timedelta
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
    # This is needed to track what the current date is
    __current_days_back = 0
    __initial_reqest = True
    URL = 'http://estadistico.ut.com.sv/OperacionDiaria.aspx'
    driver = None
    TRANSLATION_DICT = {
        'Biomasa': 'Biomass',
        'Geotérmico': 'Geothermal',
        'Hidroeléctrico': 'HydroElectric',
        'Interconexión': 'Interconnection',
        'Solar': 'Solar',
        'Térmico': 'Thermal'
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
                os.chown(full_path + chrome_driver, 0o777)
            else:
                chrome_driver = '/drivers/linux_chromedriver86_64bit'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()

    def today(self) -> list:
        today = datetime.date.today()
        return self.date(today.year, today.month, today.day)

    def yesterday(self) -> list:
        yesterday = datetime.date.today() - timedelta(days=1)
        return self.date(yesterday.year, yesterday.month, yesterday.day)

    def date(self, year, month, day) -> list:
        # I'm rewritting this becuase before it would be
        # incredibly more efficient to scroll down all at once than
        # to reload the page one day at a time
        today = datetime.date.today()
        delta = (today - datetime.date(year, month, day)).days
        delta -= self.__current_days_back
        if -delta > self.__current_days_back:
            print("date is in the future; loading present")
            delta = -(self.__current_days_back)
        if bool(delta):
            self.__request_days_back(delta)
        return self.scrape_data()

    def date_range(self, start_year, start_month, start_day,
                   end_year, end_month, end_day) -> list:
        # I changed a few things, basically to work top-down.
        # Working in this way due to how the website is structered.
        # THIS IS MUCH BETTER THAN FOWRARD - TRUST ME
        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day)
        delta = (datetime.date.today() - end_date).days
        delta -= self.__current_days_back
        if -delta > self.__current_days_back:
            print("date is in the future; loading present")
            delta = -(self.__current_days_back)
        data_points = []
        if bool(delta):
            self.__request_days_back(delta + 1)
            data_points.extend(self.scrape_data())
            start_date += datetime.timedelta(days=1)
        while start_date <= end_date:
            self.__request_days_back(1)
            data_points.extend(self.scrape_data())
            start_date += datetime.timedelta(days=1)
        return data_points

    def __request_days_back(self, days_back: int):
        """
        Requests n days back on the Daily Operation's page and reloads it
        """
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-icon-dashboard-parameters')))
        button = self.driver.find_element_by_class_name(
            'dx-icon-dashboard-parameters')
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element(button)
        action.click(on_element=button)
        action.perform()
        action.reset_actions()

        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-dropdowneditor-icon')))
        dropdown = self.driver.find_element_by_class_name(
            'dx-dropdowneditor-icon')
        action.move_to_element(dropdown)
        action.click(on_element=dropdown)
        action.release()
        action.perform()
        self.__key_down_element(days_back, dropdown)

    def __key_down_element(self, times: int, element):
        """
        Helper function to focus on element and click the down arrow n times
        """
        action = selenium.webdriver.ActionChains(self.driver)
        key_action = Keys.DOWN
        self.__current_days_back += times
        if (times < 0):
            key_action = Keys.UP
            times *= -1
        if self.__initial_reqest:
            self.__initial_reqest = False
            action.send_keys(key_action)
        for i in range(0, times):
            action.send_keys(key_action)
        action.send_keys(Keys.RETURN)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.TAB)
        action.send_keys(Keys.RETURN)
        action.perform()

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

    def __data_point(self, date, value, production_type) -> dict:
        return {'ts': date,
                'value': float(value),
                'ba': 'Unidad de Transacciones',
                'meta': production_type + ' (MWh)'}


def main():
    el_salvador = ElSalvador()

    print("Loading Today...")
    today = el_salvador.today()
    for datapoint in today:
        print(datapoint)

    print("Loading Yesterday...")
    yesterday = el_salvador.yesterday()
    for datapoint in yesterday:
        print(datapoint)

    print("Loading date...")
    day = el_salvador.date(2020, 11, 10)
    for datapoint in day:
        print(datapoint)

    print("Loading date range...")
    days = el_salvador.date_range(2020, 11, 8, 2020, 11, 9)
    for datapoint in days:
        print(datapoint)


if __name__ == "__main__":
    main()
