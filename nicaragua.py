import datetime
from datetime import timedelta
import dateutil
import arrow
import platform
import re
from bs4 import BeautifulSoup
import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Nicaragua:

    URL = 'http://www.cndc.org.ni/consultas/reportesDiarios/postDespachoEnergia.php?fecha='
    BA = 'Centro Nacional de Despacho de Carga'
    driver = None

    def __init__(self):
        options = Options()
        options.headless = True
        operating_system = platform.system()
        chrome_driver = './drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = './drivers/linux_chromedriver86'
        elif operating_system == "Darwin":
            chrome_driver = './drivers/mac_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = './drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=chrome_driver)

    def __del__(self):
        self.driver.quit()

    def search_date(self, date='') -> list:
        """
        :param date: If empty, yesterday is default
            Enter 'DD/MM/YYYY' for date to retrieve data from other dates.
        :return: a list of dictoinaries.
        """

        if not bool(date):
            yesterday = datetime.date.today() - timedelta(days=1)
            # reformatted date to match costa ricas search 'DD/MM/YYYY'
            date = (str(yesterday.day).zfill(2) + "/" +
                    str(yesterday.month).zfill(2) + "/" +
                    str(yesterday.year).zfill(4))

        url = Nicaragua.URL + date + "&d=1"
        self.driver.get(url)

        timeout = 10
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.XPATH, '//div[@id="Postdespacho"]//table[@id="GeneracionXAgente"]')))

        tableDate = self.driver.find_element_by_id('dtpFechaConsulta').get_attribute('value')
        tabs = self.driver.find_element_by_class_name('tabs').find_elements_by_tag_name('table')
        tabs[1].click()

        return self.__scrape_data(self.driver, date, tableDate)

    def __scrape_data(self, driver, date, tableDate) -> list:
        soup = BeautifulSoup(driver.page_source, "html5lib")

        tab = soup.find('div', {'id': 'Postdespacho'})
        plants_hours = tab.find('table', {'id': 'GeneracionXAgente'}).findAll('tr')
        headerCells = plants_hours[1].findAll('td')

        data_points_list = []
        for row in range(2, len(plants_hours)):
            rowEntry = plants_hours[row].findAll('td')
        #data starts on 1 since 0 is just the hour, skip last since it's just total
        for column in range(1, len(rowEntry) - 1):
            value = rowEntry[column].getText()
            header = headerCells[column - 1].getText()
            hour = rowEntry[0].getText()
            #if value is empty, put a 0
            if not bool(value):
                value = '0'
            data_points_list.append(self.__data_point(header, tableDate, hour, value))

        return data_points_list


    def __data_point(self, location: str, todaysDate: str, hour: int, value: float) -> dict:
        datapoint = {}
        datapoint['ts'] = arrow.get(todaysDate + str(hour).zfill(2) + ":00",
            'DD/MM/YYYYHH:mm',
            locale="es", tzinfo=dateutil.tz.gettz('America/Managua')).datetime
        datapoint['value'] = value
        datapoint['ba'] = Nicaragua.BA
        datapoint['meta'] = location + " (MWh)"
        return datapoint

def main():
    print("Initializing driver...")
    nicaragua = Nicaragua()

    print("Loading yesterday...")
    yesterday_data = nicaragua.search_date()
    for datapoint in yesterday_data:
        print(datapoint)

    print("Loading other date...")
    other_date_data = nicaragua.search_date('03/11/2020')
    for datapoint in other_date_data:
        print(datapoint)

if __name__ == "__main__":
    main()