import selenium
import re
import datetime
from datetime import timedelta
import arrow
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# change driver depending on OS and Web Browser (Mac and Chrome default)
DRIVER_PATH = './drivers/chromedriver'
URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
BA = 'Operación Sistema Eléctrico Nacional'

options = Options()
options.headless = True
driver = selenium.webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
driver.get(URL)


def scrape_date(date="") -> list:
    if not bool(date):
        date = str(datetime.date.today() - timedelta(days=1))

    driver.find_element_by_name("formPosdespacho:txtFechaInicio_input").send_keys(Keys.RETURN)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    cells = soup.find('tbody', {'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
    list = []
    for cell in cells:
        if cell.has_attr('title') and bool(cell.getText()) and 'Total' not in cell['title']:
            list.append(get_data_point(date, cell))
    return list


def get_data_point(date: str, data: BeautifulSoup) -> dict:
    location = re.search(r'(.*?),(.*)', data['title']).group(1)
    time = re.search(r'(.*?),(.*)', data['title']).group(2)
    time_stamp = arrow.get(date + time, 'YYYY-MM-DD HH:mm', locale="es", tzinfo='America/Costa_Rica').strftime("%Y-%-m-%-d %H:%M")
    return {'ts': time_stamp,
            'value': data.getText(),
            'ba': BA,
            'meta': location + " (MWh)"}


def main():
    for datapoint in scrape_date():
        print(datapoint)


if __name__ == "__main__":
    main()
