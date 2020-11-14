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

"""
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
"""


class CostaRica:
    """
    This class uses only the public method search_date() to retrive data.
    Other methods are private helpers and are not called from client.
    Automattically initalizes web driver based on users OS
    """
    URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    driver = None

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
        self.driver.get(CostaRica.URL)

    def __del__(self):
        self.driver.quit()

    def today(self):
        return self.yesterday(0)

    def yesterday(self, day=1):
        yesterday = datetime.date.today() - timedelta(days=day)
        # reformatted date to match costa ricas search 'DD/MM/YYYY'
        date = (str(yesterday.day).zfill(2) + "/" +
                str(yesterday.month).zfill(2) + "/" +
                str(yesterday.year).zfill(4))

        search_date_field = self.driver.find_element_by_name(
            "formPosdespacho:txtFechaInicio_input")
        search_date_field.clear()
        search_date_field.send_keys(date + Keys.RETURN)
        return self.__scrape_data(self.driver, date)


    def last_number_of_days(self, days):
        for day in range(days):
            self.yesterday(day)

    def date(self, date='') -> list:
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

        search_date_field = self.driver.find_element_by_name(
            "formPosdespacho:txtFechaInicio_input")
        search_date_field.clear()
        search_date_field.send_keys(date + Keys.RETURN)
        return self.__scrape_data(self.driver, date)

    def date_range(self):
        pass

    def year(self):
        pass


    def __scrape_data(self, driver, date) -> list:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        plants_hours = soup.find('tbody', {
            'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
        data_points_list = []
        for plant_hour in plants_hours:
            if (plant_hour.has_attr('title') and bool(plant_hour.getText())
                    and 'Total'not in plant_hour['title']):
                data_points_list.append(self.__data_point(date, plant_hour))
        return data_points_list

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
    #today = costa_rica.today()
    #for datapoint in today:
    #    print(datapoint)

    #yesterday = costa_rica.yesterday()
    #for datapoint in yesterday:
    #    print(datapoint)

    for days in range(10):
        for datapoint in costa_rica.yesterday(days):
            print(datapoint)

    #print("Loading yesterday...")
    #yesterday_data = costa_rica.date()
    #for datapoint in yesterday_data:
    #    print(datapoint)

    #print("Loading other date...")
    #other_date_data = costa_rica.date('14/11/2020')
    #for datapoint in other_date_data:
    #    print(datapoint)




if __name__ == "__main__":
    main()
