import datetime
import platform
import re
from datetime import timedelta
from pathlib import Path

import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class Mexico:
    URL = ('https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx')
    download_dir = "/downloads"
    driver = None
    TRANSLATION_DICT = {
        'Biomasa': 'Biomass',
        'Geotérmico': 'Geothermal',
        'Hidroeléctrico': 'HydroElectric',
        'Interconexión': 'Interconnection',
        'Solar': 'Solar',
        'Térmico': 'Thermal'
    }

    def __init__(self):
        # path = os.path.abspath(__file__ + "/../")
        # path = path + '/drivers/win_chromedriver86.exe'
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
    
    def scrape(self):
        download = self.driver.find_element_by_id("ct100_ContentPlaceHolder1_DescargarReportes")
        download.click()


def main():
    print("Initializing driver...")
    mexico = Mexico()
    mexico.scrape()


if __name__ == "__main__":
    main()