


import datetime
import platform
from pathlib import Path

import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class ElSalvador:

    URL = 'http://estadistico.ut.com.sv/OperacionDiaria.aspx'
    BA = 'Unidad de Transacciones'
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
        full_path = str(__file__)
        full_path = str(Path(full_path).parents[0])
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = '/drivers/linux_chromedriver86'
        elif operating_system == "Darwin":
            chrome_driver = '/drivers/mac_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(ElSalvador.URL)

    def __del__(self):
        self.driver.quit()

    def scrape_data(self) -> list:
        """
        Grabs the daily report for El Salvador.

        Return: list of datapoints
        """
        self.driver
        timeout = 10
        WebDriverWait(self.driver, timeout).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-word-wrap')))

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        generation_table = soup.find('table', {'class': 'dx-word-wrap'})
        table_headers = generation_table.find(
            'td',
            {'class': 'dx-area-column-cell'})
        columns = table_headers.find('table').find_all('span')
        columns = columns[0:-1]
        for i in range(0, len(columns)):
            columns[i] = columns[i].text

        data_table = generation_table.find('tr', {'class': 'dx-bottom-row'})
        times = data_table.find(
            'td',
            {'class': 'dx-area-row-cell'}).find_all('span')
        data = data_table.find(
            'td',
            {'class': 'dx-area-data-cell'}).find('table')
        scrape_date = times[1].text
        hours = times[2:-1]
        for i in range(0, len(hours)):
            hours[i] = hours[i].text
        datapoints = []
        entries = data.find_all('tr')
        entries = entries[0:-1]
        for row in range(0, len(entries)):
            cells = entries[row].find_all('td')
            cells = cells[0:-1]
            for i in range(0, len(cells)):
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
                datapoints.append(
                    self.__data_point(date, value, production_type))
        return datapoints

    def __data_point(
        self,
        date: datetime,
        value: str,
        production_type: str
    ) -> dict:
        """
        Parameters:
            date -- datetime object for datapoint (realative timezone)
            value -- float value of electricity production in MWh
            production_type -- string that contains the production type

        Return: dictionary (format defined by WattTime)
        """
        return {
            'ts': date,
            'value': float(value),
            'ba': self.BA,
            'meta': production_type + ' (MWh)'
        }


def main():
    scraper = ElSalvador()
    for data in scraper.scrape_data():
        print(data)


if __name__ == "__main__":
    main()
