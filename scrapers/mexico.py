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

import zipfile
import pandas as pd


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

    def __init__(self):
        options = webdriver.ChromeOptions()
        # options.headless = True
        operating_system = platform.system()
        self.directory = str(Path(str(__file__)).parents[0])
        prefs = {"download.default_directory" : self.directory}
        options.add_experimental_option("prefs",prefs)
        chrome_driver = '/drivers/mac_chromedriver86'
        if operating_system == "Linux":
            chrome_driver = '/drivers/linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver86.exe'
        self.driver = selenium.webdriver.Chrome(
            chrome_options=options,
            executable_path=(self.directory + chrome_driver))
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()

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

    def __format_query(self, date):
        temp = date.split('/')
        month = self.MONTHS[int(temp[1]) - 1]
        year = temp[2]
        return month + ' de ' + year

    def __retrieve_files(self, initial_date, final_date):
        try:
            print('Downloading zip file...')
            # TODO check validity of date
            start = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaInicial_dateInput")
            start.clear()
            start.send_keys(self.__format_query(initial_date))
            stop = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_FechaFinal_dateInput")
            stop.clear()
            stop.send_keys(self.__format_query(final_date))
            self.__manual_click('DescargaZip')

            # wait for file to finish downloading
            zip_exists = False
            while not zip_exists:
                action = selenium.webdriver.ActionChains(self.driver)
                action.pause(1)
                action.perform()
                action.reset_actions()
                for filename in os.listdir(self.directory):
                    if filename.endswith('.zip'):
                        zip_exists = True
                        break

            print('Extracting files...')
            for filename in os.listdir(self.directory):
                if filename.endswith(".zip"):
                    self.__unzip(filename)
                    # delete zip file
                    # os.remove(self.directory + '/' + filename)

        except selenium.common.exceptions.NoSuchElementException:
            print("Button not found!")

    # write date in dd/mm/yyyy format
    def scrape(self, initial_date, final_date):
        self.__retrieve_files(initial_date, final_date)

        for filename in os.listdir(self.directory):
            if filename.endswith(".csv"):
                path = self.directory + '/' + filename
                df = pd.read_csv(path, skiprows=7)
                
                # TODO grab and format data

                for index, row in df.iterrows():\
                    pass
                    # grab col 2 and 3 and create date
                    # for columns 4 - last
                        # create datapoint(date, value, column header)

                #delete csv file
                # os.remove(path)

    def __unzip(self, filename):
        path = self.directory + '/' + filename
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(self.directory)

    def __data_point(self, date, value, production_type) -> dict:
        return {'ts': date,
                'value': float(value),
                'ba': 'CENACE', # TODO ask connor for clarification
                'meta': self.TRANSLATION_DICT[production_type] + ' (MWh)'}


def main():
    print("Initializing driver...")
    scraper = Mexico()

    print("Scraping data...")
    scraper.scrape('12/08/2020', '12/10/2020')


if __name__ == "__main__":
    main()