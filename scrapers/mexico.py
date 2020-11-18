import datetime
import platform
import re
from datetime import timedelta
from pathlib import Path

import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import os


class Mexico:
    URL = 'https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx'
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
        options = Options()
        # options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        argument = "download.default_directory=" + full_path + '/downloads'
        options.add_argument(argument)
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = '/drivers/linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(self.URL)
        
        # cwd = os.path.abspath(__file__ + "/../")
        # driver_dir = cwd + '/drivers/win_chromedriver86.exe'
        # download_dir = cwd + "/downloads"
        # try:
        #     os.makedirs(download_dir)
        # except FileExistsError:
        #     pass

        # options = webdriver.ChromeOptions()
        # #options.add_argument('headless')
        # prefs = {}
        # prefs["download.default_directory"]=download_dir
        # options.add_experimental_option("prefs", prefs)

        # self.driver = webdriver.Chrome(
        #     chrome_options=options,
        #     executable_path=driver_dir
        # )
        # self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()

    def __manual_click(self, element, wait=0):
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.ID, element)))
        button = self.driver.find_element_by_id(element)
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element(button)
        action.click(on_element=button)
        if(wait > 0):
            action.pause(wait)
        action.perform()
        action.reset_actions()

    def scrape(self):
        try:
            self.__manual_click('ctl00_ContentPlaceHolder1_FechaInicial_popupButton')
            self.__manual_click('rcMView_sep.')
            self.__manual_click('rcMView_OK')
            self.__manual_click('ctl00_ContentPlaceHolder1_FechaFinal_popupButton')
            self.__manual_click('rcMView_oct.')
            self.__manual_click('rcMView_OK')
            print('Downloading file...')
            self.__manual_click('DescargaZip', 10)

        except selenium.common.exceptions.NoSuchElementException:
            print("Button not found!")


def main():
    print("Initializing driver...")
    mexico = Mexico()
    print("Scraping data...")
    mexico.scrape()


if __name__ == "__main__":
    main()