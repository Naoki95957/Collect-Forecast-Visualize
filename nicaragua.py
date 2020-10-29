import selenium
import datetime
import dateutil
import arrow
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

DRIVER_PATH = './driver/chromedriver86.exe'
URL = 'http://www.cndc.org.ni/consultas/reportesDiarios/postDespachoEnergia.php?fecha='
BA = 'Centro Nacional de Despacho de Carga'

def nicaraguaScraper(date="tr") -> list:
    """
    Scraper for Nicaragua
    
    This required selenium and some waiting for pages to load
    
    After that it was somewhat straight forward

    Will raise a timeout exception is timeout of 10s is surpased
    
    Returns a list of dictionaries as per WattTime spec

    Parameters:

    date -- str by default grabs the most recent date nicaragua reports (This isn't always avaible on their own website)
    You can change this to what ever previous date you wanna look at in the form DD/MM/YYYY as a string 
    """
    #set up URL
    url = URL + date + "&d=1"

    #set up a few options for selenium
    options = Options()
    options.headless = True

    #start up selenium
    driver = selenium.webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
    driver.get(url)

    timeout = 10
    #the php script takes a second to load everything in
    #this waits the timeout period while waiting for table to load
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, "GeneracionXAgente")))

    #find date box
    tableDate = driver.find_element_by_id('dtpFechaConsulta').get_attribute('value')

    #find the tabs (ul element) and get tags
    tabs = driver.find_element_by_class_name('tabs').find_elements_by_tag_name('table')
    #click the second tab
    tabs[1].click()

    #soup time
    soup = BeautifulSoup(driver.page_source, "html5lib")
    table = soup.find('table', {'id': 'GeneracionXAgente'}).findAll('tr')

    outputList = []
    #just header info on row 0 and 1
    #we will use header line 1
    #data starts on 2
    #headers are actually OFFSET BY ONE, so we'll need to remember that
    headerCells = table[1].findAll('td')
    for row in range(2, len(table)):
        rowEntry = table[row].findAll('td')
        #data starts on 1 since 0 is just the hour, skip last since it's just total
        for column in range(1, len(rowEntry) - 1):
            value = rowEntry[column].getText()
            header = headerCells[column - 1].getText()
            hour = rowEntry[0].getText()
            #if value is empty, put a 0
            if not bool(value):
                value = '0'
            outputList.append(formatter(header, tableDate, hour, value))
        
    driver.quit()

    return outputList

def formatter(location: str, todaysDate: str, hour: int, value: float) -> dict:
    """
    Helper function to format the data from soup

    returns a dictionary in WattTime spec

    parameters:

    todaysDate -- should be a dateTime obj with todays date. hour doesn't matter

    data -- should be a soupy object. Specifically the cell entry
    """
    datapoint = {}
    datapoint['ts'] = arrow.get(todaysDate + str(hour).zfill(2) + ":00", 'DD/MM/YYYYHH:mm', locale="es", tzinfo=dateutil.tz.gettz('America/Managua')).datetime
    datapoint['value'] = value
    datapoint['ba'] = BA
    datapoint['meta'] = location + " (MWh)"
    return datapoint

def main():
    for datapoint in nicaraguaScraper():
        print(datapoint)

if __name__ == "__main__":
    main()