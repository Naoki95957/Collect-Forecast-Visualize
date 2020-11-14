"""

    This class retrives all emission data from Nicargua.
    Emissions are reporte by hour, MWh, BA, and includes power plant name.
    Methods yesterday, date, and date range return a list of dictionaries.
    Nicargua most recent data available is yesterday, today is not available.


    This class dependency uses chrome webdrivers located in the drivers folder.
    The class automatically detects OS and navigates an invisible browser.
    Initilizing driver takes longer than retriving date.
    Use date_range for multiple days instead of initilizing driver for each date.

    If program doesn't run in MAC, try opening mac_chromedriver86 in drivers folder
    If you get a warning:
        “mac_chromedriver86” can’t be opened because the identity of the developer
        cannot be confirmed."
    Go to Apple > System Preferences > Security & Privacy and click the
        'Open Anyway' button. Then rerun program.
    To update drivers:
    https://selenium-python.readthedocs.io/installation.html
"""

import datetime
import platform
from datetime import timedelta
from pathlib import Path

import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class Nicaragua:
    URL = ('http://www.cndc.org.ni/consultas/reportesDiarios/'
           'postDespachoEnergia.php?fecha=')
    driver = None
    data_points = []

    def __init__(self):
        options = Options()
        options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = '/drivers/linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))

    def __del__(self):
        self.driver.quit()

    def yesterday(self) -> list:
        yesterday = datetime.date.today() - timedelta(days=1)
        return self.date(yesterday.year, yesterday.month, yesterday.day)

    def date(self, year, month, day) -> list:
        return self.date_range(year, month, day, year, month, day)

    def date_range(self, start_year, start_month, start_day,
                   end_year, end_month, end_day) -> list:
        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day + 1)
        while start_date < end_date:
            # Reformat date to match search field
            date = (str(start_date.day).zfill(2) + "/" +
                    str(start_date.month).zfill(2) + "/" +
                    str(start_date.year).zfill(4))
            self.driver.get(self.URL + date + "&d=1")
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((
                    By.XPATH, ('//div[@id="Postdespacho"]/'
                               '/table[@id="GeneracionXAgente"]'))))
            table_date = self.driver.find_element_by_id(
                'dtpFechaConsulta').get_attribute('value')
            tabs = self.driver.find_element_by_class_name(
                'tabs').find_elements_by_tag_name('table')
            tabs[1].click()
            self.__scrape_data(table_date)
            start_date += datetime.timedelta(days=1)
        return self.data_points

    def __scrape_data(self, table_date):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        tab = soup.find('div', {'id': 'Postdespacho'})
        plants_hours = tab.find(
            'table', {'id': 'GeneracionXAgente'}).findAll('tr')
        location_cells = plants_hours[1].findAll('td')
        for row in range(2, len(plants_hours)):
            row_entry = plants_hours[row].findAll('td')
            for column in range(1, len(row_entry) - 1):
                value = row_entry[column].getText()
                location = location_cells[column - 1].getText()
                hour = row_entry[0].getText()
                if not bool(value):
                    value = '0'
                self.data_points.append(self.__data_point(location, table_date, hour, value))

    def __data_point(self, location, todays_date, hour, value) -> dict:
        return {'ts': arrow.get(todays_date + str(hour).zfill(2) + ":00",
                                'DD/MM/YYYYHH:mm',
                                locale="es",
                                tzinfo='America/Managua').datetime,
                'value': float(value),
                'ba': 'Centro Nacional de Despacho de Carga',
                'meta': location + " (MWh)"}


def main():
    print("Initializing driver...")
    nicaragua = Nicaragua()

    print("Loading Yesterday...")
    yesterday = nicaragua.yesterday()
    for datapoint in yesterday:
        print(datapoint)

    print("Loading date...")
    day = nicaragua.date(2020, 11, 10)
    for datapoint in day:
        print(datapoint)

    print("Loading date range...")
    days = nicaragua.date_range(2020, 11, 10, 2020, 11, 12)
    for datapoint in days:
        print(datapoint)


if __name__ == "__main__":
    main()
