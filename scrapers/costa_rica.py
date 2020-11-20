"""
    This class retrives Real Generation, MWh from all Costa Rica's power
    plants by hour. It uses chrome webdrivers to navigate the website.
    Initilizing driver takes longer than retriving date. Use date_range for
    multiple days instead of constructing class and initilizing driver for
    each date.

    If program doesn't run in MAC, open mac_chromedriver86 in drivers folder
    If you get a warning:
        “mac_chromedriver86” can’t be opened because the identity of the
        developer cannot be confirmed."
    Go to Apple > System Preferences > Security & Privacy and click the
        'Open Anyway' button. Then rerun program.

    To update drivers:
    https://selenium-python.readthedocs.io/installation.html
"""


import datetime
import platform
import re
from datetime import timedelta
from pathlib import Path

import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class CostaRica:
    URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    driver = None

    def __init__(self):
        options = Options()
        options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            architecture = platform.architecture()[0]
            if architecture == '32bit':
                chrome_driver = '/drivers/linux_chromedriver_65_32bit'
            else:
                chrome_driver = '/drivers/linux_chromedriver86'
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
        return self.date_range(year, month, day, year, month, day)

    def date_range(self, start_year, start_month, start_day,
                   end_year, end_month, end_day) -> list:
        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day)
        all_data_points = []
        while start_date <= end_date:
            # Reformat date to match costa rica's search field
            date = (str(start_date.day).zfill(2) + "/" +
                    str(start_date.month).zfill(2) + "/" +
                    str(start_date.year).zfill(4))
            search_date_field = self.driver.find_element_by_name(
                "formPosdespacho:txtFechaInicio_input")
            search_date_field.clear()
            search_date_field.send_keys(date + Keys.RETURN)
            all_data_points.extend(self.__scrape_data(date))
            start_date += datetime.timedelta(days=1)
        return all_data_points

    def __scrape_data(self, date) -> list:
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        plants_hours = soup.find('tbody', {
            'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
        date_data_points = []
        for plant_hour in plants_hours:
            if (plant_hour.has_attr('title') and bool(plant_hour.getText())
                    and 'Total' not in plant_hour['title']):
                date_data_points.append(self.__data_point(date, plant_hour))
        return date_data_points

    def __data_point(self, date, plant_hour) -> dict:
        plant = re.search(r'(.*?),(.*)', plant_hour['title']).group(1)
        emission_hour = re.search(r'(.*?),(.*)', plant_hour['title']).group(2)
        time_stamp = arrow.get(
            date + emission_hour,
            'DD/MM/YYYY HH:mm',
            locale="es",
            tzinfo='America/Costa_Rica').datetime
        return {'ts': time_stamp,
                'value': float(plant_hour.getText()),
                'ba': 'Operación Sistema Eléctrico Nacional',
                'meta': plant + " (MWh)"}


def main():
    print("Initializing driver...")
    costa_rica = CostaRica()

    print("Loading Today...")
    today = costa_rica.today()
    for datapoint in today:
        print(datapoint)

    print("Loading Yesterday...")
    yesterday = costa_rica.yesterday()
    for datapoint in yesterday:
        print(datapoint)

    print("Loading date...")
    day = costa_rica.date(2020, 9, 30)
    for datapoint in day:
        print(datapoint)

    print("Loading date range...")
    days = costa_rica.date_range(2020, 10, 30, 2020, 11, 1)
    for datapoint in days:
        print(datapoint)


if __name__ == "__main__":
    main()
