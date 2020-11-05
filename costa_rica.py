import selenium
import re
import datetime
from datetime import timedelta
import arrow
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# change drivers depending on OS and Web Browser (Mac and Chrome default)
DRIVER_PATH = './drivers/chromedriver'
URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
BA = 'Operación Sistema Eléctrico Nacional'

options = Options()
options.headless = True
driver = selenium.webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
driver.get(URL)


def scrape_date(date="") -> list:
    if not bool(date):  # get yesterdays data by default
        yesterday = datetime.date.today() - timedelta(days=1)
        date = str(yesterday.day).zfill(2) + "/" + str(yesterday.month).zfill(2) + "/" + str(yesterday.year).zfill(4)
    search_date = driver.find_element_by_name("formPosdespacho:txtFechaInicio_input")
    search_date.clear()
    search_date.send_keys(date + Keys.RETURN)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    cells = soup.find('tbody', {'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
    list = []
    for cell in cells:
        if cell.has_attr('title') and bool(cell.getText()) and 'Total' not in cell['title']:
            list.append(get_data_point(date, cell))
    return list


def get_data_point(date: str, soup: BeautifulSoup) -> dict:
    location = re.search(r'(.*?),(.*)', soup['title']).group(1)
    time = re.search(r'(.*?),(.*)', soup['title']).group(2)
    date_time = arrow.get(date + time, 'DD/MM/YYYY HH:mm', locale="es", tzinfo='America/Costa_Rica').datetime
    return {'ts': date_time,
            'value': float(soup.getText()),
            'ba': BA,
            'meta': location + " (MWh)"}


def main():
    for datapoint in scrape_date():
        print(datapoint)


if __name__ == "__main__":
    main()
