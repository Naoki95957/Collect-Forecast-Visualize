import selenium
import re
import datetime
import arrow
import platform
from datetime import timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from pathlib import Path

'''
Retrives emission data as a list of dictionaries from Costa Rica by hours
for each plant and balance authority name.

If program doesn't run in MAC, try opening mac_chromedriver86 in drivers folder
If you get a warning:
    “mac_chromedriver86” can’t be opened because the identity of the developer
    cannot be confirmed."
Go to Apple > System Preferences > Security & Privacy and click the
    'Open Anyway' button. Then rerun program.
To update drivers:
https://selenium-python.readthedocs.io/installation.html
'''


class CostaRica:
    """
    This class uses only the public method search_date() to retrive data.
    Other methods are private helpers and are not called from client.
    Automattically initalizes web driver based on users OS
    """
    URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    driver = None
    data_points_list = []

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

    def today(self):
        today = datetime.date.today()
        self.date(today.year, today.month, today.day)
        return self.data_points_list

    def yesterday(self):
        yesterday = datetime.date.today() - timedelta(days=1)
        self.date(yesterday.year, yesterday.month, yesterday.day)
        return self.data_points_list

    def date(self, year, month, day):
        self.date_range(year, month, day, year, month, day)
        return self.data_points_list

    def date_range(self, start_year, start_month, start_day,
                   end_year, end_month, end_day):
        start_date = datetime.date(start_year, start_month, start_day)
        end_date = datetime.date(end_year, end_month, end_day + 1)
        while start_date < end_date:
            # Reformat date to match costa rica's search field
            date = (str(start_date.day).zfill(2) + "/" +
                    str(start_date.month).zfill(2) + "/" +
                    str(start_date.year).zfill(4))
            search_date_field = self.driver.find_element_by_name(
                "formPosdespacho:txtFechaInicio_input")
            search_date_field.clear()
            search_date_field.send_keys(date + Keys.RETURN)
            self.__scrape_data(date)
            start_date += datetime.timedelta(days=1)
        return self.data_points_list

    def __scrape_data(self, date):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        plants_hours = soup.find('tbody', {
            'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
        for plant_hour in plants_hours:
            if (plant_hour.has_attr('title') and bool(plant_hour.getText())
                    and 'Total' not in plant_hour['title']):
                self.data_points_list.append(self.__data_point(date, plant_hour))

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
    day = costa_rica.date(2020, 11, 10)
    for datapoint in day:
        print(datapoint)

    print("Loading date range...")
    days = costa_rica.date_range(2020, 11, 10, 2020, 11, 12)
    for datapoint in days:
        print(datapoint)


if __name__ == "__main__":
    main()
