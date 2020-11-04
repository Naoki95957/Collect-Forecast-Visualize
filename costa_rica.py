import selenium
import re
import datetime
import dateutil
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


def costaRicaScraper(date="") -> list:
    if not bool(date):
        todays_date = datetime.date.today()
        date = str(todays_date.day).zfill(2) + "/" + str(todays_date.month).zfill(2) + "/" + str(
            todays_date.year).zfill(4)
    # clear the field and put in today's date
    input_field = driver.find_element_by_name("formPosdespacho:txtFechaInicio_input")
    input_field.clear()
    input_field.send_keys(date + Keys.RETURN)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cells = soup.find('tbody', {'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')

    output_list = []
    for cell in cells:
        if cell.has_attr('title') and bool(cell.getText()):
            if 'Total' not in cell['title']:
                output_list.append(formatter(date, cell))
    driver.quit()
    return output_list


def formatter(todaysDate: str, data: BeautifulSoup) -> dict:
    # parse out the location and hour of each cell
    location = re.search(r'(.*?),(.*)', data['title']).group(1)
    time = re.search(r'(.*?),(.*)', data['title']).group(2)
    return {'ts': arrow.get(todaysDate + time, 'DD/MM/YYYY HH:mm').datetime,
            'value': data.getText(),
            'ba': BA,
            'meta': location + " (MWh)"}

"""
    spanish_time = soup.find('div', {'class': 'sitr-update'}).find_all('span')[0].get_text()
    time_stamp_sp = arrow.get(spanish_time, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    time_stamp_en = time_stamp_sp.datetime.strftime("%Y-%-m-%-d %H:%M:%S")


datapoint1 = \
 {'ts': <timezone aware datetime object>,
  'value': <value of grid parameter (type float or int)>,
  'ba': <string specifying balancing authority or subregion eg 'PJM_WEST', 'NL' for Netherlands, 'ISONE_VERMONT'>,
  'meta': <optional field specifying fuel type (if generation) or other information
"""


def main():
    for datapoint in costaRicaScraper():
        print(datapoint)


if __name__ == "__main__":
    main()
