import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import re
import datetime
from datetime import timedelta
import arrow
from bs4 import BeautifulSoup
import platform

"""
Retrives emission data as a list of dictionaries from Costa Rica by hours
for each plant and balance authority name.

If program doesn't run in MAC, try opening mac_chromedriver86 in drivers folder.
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
    """
    URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    driver = None

    def __init__(self):
        self.__initialize_OS_driver()

    def __del__(self):
        self.driver.quit()

    def __initialize_OS_driver(self) -> selenium.webdriver.Chrome:
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
        driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=chrome_driver)
        driver.get(CostaRica.URL)
        return driver


    def search_date(self, date=''):
        """
        :param date: Enter 'DD/MM/YYYY' for date_query to retrieve data from other dates.
             If empty, yesterday is default
        :return: Reformatted date to match costa ricas search 'DD/MM/YYYY'
        """
        if self.driver is None:
            self.driver = CostaRica.__initialize_OS_driver(self)
        if not bool(date):
            yesterday = datetime.date.today() - timedelta(days=1)
            date = (str(yesterday.day).zfill(2) + "/" +
                    str(yesterday.month).zfill(2) + "/" +
                    str(yesterday.year).zfill(4))
        else:
            try:  # checks valid date entered
                arrow.get(date, 'DD/MM/YYYY')
            except Exception as e:
                self.driver.quit()
                raise e

        search_date_field = self.driver.find_element_by_name(
            "formPosdespacho:txtFechaInicio_input")
        search_date_field.clear()
        search_date_field.send_keys(date + Keys.RETURN)
        return self.__scrape_data(self.driver, date)


    def __scrape_data(self, driver: selenium.webdriver.Chrome, date: datetime) -> list:
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
    costa_rica = CostaRica()

    yesterday_data = costa_rica.search_date()
    for datapoint in yesterday_data:
        print(datapoint)

    other_date_data = costa_rica.search_date('03/11/2020')
    for datapoint in other_date_data:
        print(datapoint)


if __name__ == "__main__":
    main()