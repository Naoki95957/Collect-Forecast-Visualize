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

import zipfile
import pandas as pd
import os
import shutil



class Mexico:
    URL = 'https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx'
    TRANSLATION_DICT = {
        'Eolica' : 'Wind',
        'Fotovoltaica' : 'Photovoltaic',
        'Biomasa': 'Biomass',
        'Carboelectrica' : 'Carboelectric',
        'Ciclo Combinado' : 'Combined Cycle',
        'Combustion Interna' : 'Internal Combustion',
        'Geotermoelectrica' : 'Geothermalelectric',
        'Hidroelectrica': 'HydroElectric',
        'Nucleoelectrica' : 'Nuclear Power',
        'Termica Convencional' : 'Conventional Thermal',
        'Turbo Gas' : 'Turbo Gas'
    }
    MONTHS = [
        'enero',
        'febrero',
        'marzo',
        'abril',
        'mayo',
        'junio',
        'julio',
        'agosto',
        'septiembre',
        'octubre',
        'noviembre',
        'diciembre'
    ]
    # should these be capitalized or should the other variables be outside the class... ?
    driver = None
    directory = ''
    downloads_dir = ''

    def __init__(self):
        self.directory = os.getcwd()
        self.directory = os.path.join(self.directory, 'scrapers')
        drivers_dir = os.path.join(self.directory, 'drivers')
        self.downloads_dir = os.path.join(self.directory, 'downloads')
        if not os.path.exists(self.downloads_dir):
            os.mkdir(self.downloads_dir)

        options = webdriver.ChromeOptions()
        options.headless = True
        prefs = {"download.default_directory" : self.downloads_dir}
        options.add_experimental_option("prefs",prefs)

        operating_system = platform.system()
        if operating_system == "Linux":
            chrome_driver = 'linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = 'win_chromedriver86.exe'
        else:
            chrome_driver = 'mac_chromedriver86'

        self.driver = selenium.webdriver.Chrome(
            chrome_options=options,
            executable_path=(os.path.join(drivers_dir, chrome_driver))
        )
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()
        shutil.rmtree(self.downloads_dir)

        # Original method, for reference
        # for filename in os.listdir(downloads_dir):
        #         if filename.endswith(".zip") or filename.endswith(".csv"):
        #             os.remove(self.directory + '/' + filename)

    def __manual_click(self, element):
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((
                By.ID, element)))
        button = self.driver.find_element_by_id(element)
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element(button)
        action.click(on_element=button)
        action.perform()
        action.reset_actions()

    def __query(self, month: int, year: int):
        return str(self.MONTHS[month - 1]) + ' de ' + str(year)

    def __retrieve_files(self, initial_month: int, initial_year: int, final_month: int, final_year: int):
        try:
            # TODO check validity of date
            # first send dates
            start = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaInicial_dateInput")
            start.clear()
            start.send_keys(self.__query(initial_month, initial_year))
            stop = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaFinal_dateInput")
            stop.clear()
            stop.send_keys(self.__query(final_month, final_year))
            # click download button
            self.__manual_click('DescargaZip')

            # wait for file to finish downloading (AKA, zip file exists in directory)
            zip_exists = False
            while not zip_exists:
                action = selenium.webdriver.ActionChains(self.driver)
                action.pause(1)
                action.perform()
                action.reset_actions()
                for filename in os.listdir(self.downloads_dir):
                    if filename.endswith('.zip'):
                        zip_exists = True
                        break

            # extract zip files
            for filename in os.listdir(self.downloads_dir):
                if filename.endswith(".zip"):
                    path = os.path.join(self.downloads_dir, filename)
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(self.downloads_dir)

        except selenium.common.exceptions.NoSuchElementException:
            print("Button not found!")

    def __data_point(self, date_time, value, production_type) -> dict:
        return {
            'ts': date_time,
            'value': float(value),
            'ba': 'CENACE', # TODO ask connor for clarification
            'meta': self.TRANSLATION_DICT[production_type] + ' (MWh)'
        }

    def scrape(self, initial_month: int, initial_year: int, final_month: int, final_year: int):
        self.__retrieve_files(initial_month, initial_year, final_month, final_year)

        data = []
        # find each csv file
        for filename in os.listdir(self.downloads_dir):
            if filename.endswith(".csv"):
                path = self.downloads_dir + '/' + filename
                df = pd.read_csv(path, skiprows=7)
                
        return data

def main():
    print("Initializing driver...")
    scraper = Mexico()

    print("Scraping data...")
    data = scraper.scrape(10, 2020, 10, 2020)
    for dp in data:
        print(dp)

if __name__ == "__main__":
    main()