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

IMPORTANT: Before running, select chromedriver for your OS.
For MAC, you may get a warning:
    “mac_chromedriver86” can’t be opened because the identity of the developer
    cannot be confirmed."
Go to Apple > System Preferences > Security & Privacy and click the
    'Open Anyway' button.
To maintain, update drivers in the future:
https://selenium-python.readthedocs.io/installation.html
"""

URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'


def initialize_driver() -> selenium.webdriver.Chrome:
    """
    Sets up driver to matching os
    """
    options = Options()
    options.headless = True
    operatingSystem = platform.system()
    SELECT_OS_CHROME_DRIVER = './drivers/mac_chromedriver86'
    if (operatingSystem == "Linux"):
        SELECT_OS_CHROME_DRIVER = './drivers/linux_chromedriver86'
    elif (operatingSystem == "Darwin"):
        SELECT_OS_CHROME_DRIVER = './drivers/mac_chromedriver86'
    elif (operatingSystem == "Windows"):
        SELECT_OS_CHROME_DRIVER = './drivers/win_chromedriver86.exe'
    driver = selenium.webdriver.Chrome(
        options=options,
        executable_path=SELECT_OS_CHROME_DRIVER)
    driver.get(URL)
    return driver


def search_date(driver: selenium.webdriver.Chrome, date=""):
    """
    :param date: Enter 'DD/MM/YYYY' to retrieve data from other dates.
        If empty, yesterday is default
    :return: Reformatted datetime date to match costa ricas search date field
        'DD/MM/YYYY' as a string
    """
    if not bool(date):
        yesterday = datetime.date.today() - timedelta(days=1)
        date = (str(yesterday.day).zfill(2)
                + "/"
                + str(yesterday.month).zfill(2)
                + "/"
                + str(yesterday.year).zfill(4))
    search_date_field = driver.find_element_by_name(
        "formPosdespacho:txtFechaInicio_input")
    search_date_field.clear()
    search_date_field.send_keys(date + Keys.RETURN)
    return date


def scrape_data(driver: selenium.webdriver.Chrome, date: datetime) -> list:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    plants_hours = soup.find('tbody', {
        'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
    data_points_list = []
    for plant_hour in plants_hours:
        if (plant_hour.has_attr('title') and bool(plant_hour.getText())
                and 'Total'not in plant_hour['title']):
            data_points_list.append(data_point(date, plant_hour))
    return data_points_list


def data_point(date, plant_hour) -> dict:
    plant = re.search(r'(.*?),(.*)', plant_hour['title']).group(1)
    emission_hour = re.search(r'(.*?),(.*)', plant_hour['title']).group(2)
    time_stamp = arrow.get(
        date + emission_hour,
        'DD/MM/YYYY HH:mm',
        locale="es",
        tzinfo='America/Costa_Rica').datetime
    return {'ts': time_stamp, 'value': float(plant_hour.getText()),
            'ba': 'Operación Sistema Eléctrico Nacional',
            'meta': plant + " (MWh)"}


def main():
    driver = initialize_driver()
    date = search_date(driver)
    data_points = scrape_data(driver, date)
    for datapoint in data_points:
        print(datapoint)
    driver.quit()


if __name__ == "__main__":
    main()
