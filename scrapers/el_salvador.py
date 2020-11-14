import datetime
from datetime import timedelta
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
    driver = None
    data_points = []
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
        end_date = datetime.date(end_year, end_month, end_day + 1)
        while start_date < end_date:
            # pass start_date into scrape_data?
            # need scrape_data to select date
            self.scrape_data()
            start_date += datetime.timedelta(days=1)
        return self.data_points

    def scrape_data(self) -> list:
        """
        Grabs the daily report for El Salvador.
        Return: list of datapoints
        """
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.CLASS_NAME, 'dx-word-wrap')))

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
        scrape_date = times[1].text
        hours = times[2:-1]
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
                self.data_points.append(
                    self.__data_point(date, value, production_type))
        return self.data_points

    def __data_point(self, date, value, production_type) -> dict:
        return {'ts': date,
                'value': float(value),
                'ba': 'Unidad de Transacciones',
                'meta': production_type + ' (MWh)'}


def main():
    el_salvador = ElSalvador()
    today = el_salvador.scrape_data()
    for datapoint in today:
        print(datapoint)

    #print("Loading Today...")
    #today = el_salvador.today()
    #for datapoint in today:
    #    print(datapoint)

    # print("Loading Yesterday...")
    # yesterday = el_salvador.yesterday()
    # for datapoint in yesterday:
    #    print(datapoint)

    # print("Loading date...")
    # day = el_salvador.date(2020, 11, 10)
    # for datapoint in day:
    #    print(datapoint)

    # print("Loading date range...")
    # days = el_salvador.date_range(2020, 11, 10, 2020, 11, 12)
    # for datapoint in days:
    #    print(datapoint)


if __name__ == "__main__":
    main()
