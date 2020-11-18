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

from zipfile import ZipFile
import pandas as pd


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
        chrome_options = webdriver.ChromeOptions()
        # options = Options()
        # options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        prefs = {"download.default_directory" : "/downloads"}
        chrome_options.add_experimental_option("prefs",prefs)
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = '/drivers/linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            chrome_options=chrome_options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(self.URL)
        
        # cwd = os.path.abspath(__file__ + "/../")
        # driver_dir = cwd + '/drivers/win_chromedriver86.exe'
        # download_dir = cwd + "/downloads"
        # try:
        #     os.makedirs(download_dir)
        # except FileExistsError:
        #     pass

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

    # TODO add date argument
    def __retrieve_files(self):
        try:
            # Originlly did everything with manual clicks
            # self.__manual_click('ctl00_ContentPlaceHolder1_FechaInicial_popupButton')
            # self.__manual_click('rcMView_sep.')
            # self.__manual_click('rcMView_OK')
            # self.__manual_click('ctl00_ContentPlaceHolder1_FechaFinal_popupButton')
            # self.__manual_click('rcMView_oct.')
            # self.__manual_click('rcMView_OK')

            # Names of all the buttons
            # rcMView_ene.    rcMView_feb.    rcMView_2016    rcMView_2021
            # rcMView_mar.    rcMView_abr.    rcMView_2017    rcMView_2022
            # rcMView_may.    rcMView_jun.    rcMView_2018    rcMView_2023
            # rcMView_jul.    rcMView_ago.    rcMView_2019    rcMView_2024
            # rcMView_sep.    rcMView_oct.    rcMView_2020    rcMView_2025
            # rcMView_nov.    rcMView_dic.

            print('Downloading .zip file...')
            start = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaInicial_dateInput")
            start.clear()
            # TODO make translation method to translate from integer date to input in spanish
            # example: 10/2020 -> octubre de 2020
            start.send_keys('agosto de 2020')
            stop = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaFinal_dateInput")
            stop.clear()
            stop.send_keys('octubre de 2020')
            # TODO check if file has been downloaded before closing  (instead of manual pause)
            self.__manual_click('DescargaZip', 20)

            print('Extracting files...')
            # TODO
            # with ZipFile('.zip', 'r') as zipObj:
            #     # Extract all the contents of zip file in current directory
            #     zipObj.extractall()

        except selenium.common.exceptions.NoSuchElementException:
            print("Button not found!")
    
    def scrape(self):
        self.__retrieve_files()
        


def main():
    print("Initializing driver...")
    mexico = Mexico()
    print("Scraping data...")
    mexico.scrape()


if __name__ == "__main__":
    main()