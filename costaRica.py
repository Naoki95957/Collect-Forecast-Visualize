import selenium
import re
import datetime
import dateutil
import arrow
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

DRIVER_PATH = './driver/chromedriver86.exe'
URL = 'https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
BA = 'Operación Sistema Eléctrico Nacional'

def costaRicaScraper() -> list:
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")

    driver = selenium.webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
    driver.get(URL)

    #find the input field for date and enter today's date
    inputField = driver.find_element_by_name("formPosdespacho:txtFechaInicio_input")
    todaysDate = datetime.date.today()
    fieldInput = str(todaysDate.day).zfill(2) + "/" + str(todaysDate.month).zfill(2) + "/" + str(todaysDate.year).zfill(4)
    inputField.clear()
    inputField.send_keys(fieldInput + Keys.RETURN)

    #soup time
    soup = BeautifulSoup(driver.page_source, "html5lib")
    cells = soup.find('tbody', {'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
    #print(soup.prettify())
    outputList = []
    for cell in cells:
        if cell.has_attr('title') and bool(cell.getText()):
            if 'Total' not in cell['title']:
                outputList.append(formatter(fieldInput, cell))
    driver.quit()

    return outputList

def formatter(todaysDate: str, data: BeautifulSoup) -> dict:
    """
    Helper function to format the data from soup

    returns a dictionary in WattTime spec

    parameters:

    todaysDate -- should be a dateTime obj with todays date. hour doesn't matter

    data -- should be a soupy object. Specifically the cell entry
    """
    location = re.search(r'(.*?),(.*)', data['title']).group(1)
    time = re.search(r'(.*?),(.*)', data['title']).group(2)

    datapoint = {}
    datapoint['ts'] = arrow.get(todaysDate + time, 'DD/MM/YYYY HH:mm', locale="es", tzinfo=dateutil.tz.gettz('America/Costa_Rica')).datetime
    datapoint['value'] = data.getText()
    datapoint['ba'] = BA
    datapoint['meta'] = location + " (MWh)"
    return datapoint

def main():
    for datapoint in costaRicaScraper():
        print(datapoint)

if __name__ == "__main__":
    main()