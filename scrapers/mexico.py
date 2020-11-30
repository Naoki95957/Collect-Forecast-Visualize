import platform
import arrow
import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import zipfile
import pandas as pd
import os
import errno
import shutil


class Mexico:
    '''
    This class scrapes the energy generation data from the files
    provided in the url. The website reports the data for an entire
    month at a time, thus it does not have data for the current
    month. It reports data by the day and the hour (24 hours per
    day). To retrieve data run the scrape method on a date range.
    '''
    URL = ('https://www.cenace.gob.mx/Paginas/'
           'SIM/Reportes/EnergiaGeneradaTipoTec.aspx')
    TRANSLATION_DICT = {
        'Eolica': 'Wind',
        'Fotovoltaica': 'Photovoltaic',
        'Biomasa': 'Biomass',
        'Carboelectrica': 'Carboelectric',
        'Ciclo Combinado': 'Combined Cycle',
        'Combustion Interna': 'Internal Combustion',
        'Geotermoelectrica': 'Geothermalelectric',
        'Hidroelectrica': 'HydroElectric',
        'Nucleoelectrica': 'Nuclear Power',
        'Termica Convencional': 'Conventional Thermal',
        'Turbo Gas': 'Turbo Gas'
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
    DRIVER = None
    DIRECTORY = ''
    DOWNLOADS_DIR = ''

    def __init__(self):
        self.DIRECTORY = os.getcwd()
        if not self.DIRECTORY.endswith('scrapers'):
            self.DIRECTORY = os.path.join(self.DIRECTORY, 'scrapers')
        drivers_dir = os.path.join(self.DIRECTORY, 'drivers')
        self.DOWNLOADS_DIR = os.path.join(self.DIRECTORY, 'mexico_downloads')
        try:
            os.mkdir(self.DOWNLOADS_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                os.remove(self.DOWNLOADS_DIR)
                os.mkdir(self.DOWNLOADS_DIR)

        options = Options()
        options.headless = True
        prefs = {"download.default_directory": self.DOWNLOADS_DIR}
        options.add_experimental_option("prefs", prefs)

        operating_system = platform.system()
        if operating_system == "Linux":
            chrome_driver = 'linux_chromedriver86'
        elif operating_system == "Windows":
            chrome_driver = 'win_chromedriver86.exe'
        else:
            chrome_driver = 'mac_chromedriver86'
            options.headless = False

        self.DRIVER = selenium.webdriver.Chrome(
            options=options,
            executable_path=(os.path.join(drivers_dir, chrome_driver))
        )
        self.DRIVER.get(self.URL)

    def __del__(self):
        self.DRIVER.quit()
        shutil.rmtree(self.DOWNLOADS_DIR)

    def __manual_click(self, element):
        WebDriverWait(self.DRIVER, 10).until(
            ec.presence_of_element_located((
                By.ID, element)))
        button = self.DRIVER.find_element_by_id(element)
        action = selenium.webdriver.ActionChains(self.DRIVER)
        action.move_to_element(button)
        action.click(on_element=button)
        action.perform()
        action.reset_actions()

    def __query(self, month: int, year: int):
        return str(self.MONTHS[month - 1]) + ' de ' + str(year)

    def __retrieve_files(self, initial_month: int, initial_year: int,
                         final_month: int, final_year: int):
        try:
            start = self.DRIVER.find_element_by_id(
                "ctl00_ContentPlaceHolder1_FechaInicial_dateInput")
            start.clear()
            start.send_keys(self.__query(initial_month, initial_year))
            stop = self.DRIVER.find_element_by_id(
                "ctl00_ContentPlaceHolder1_FechaFinal_dateInput")
            stop.clear()
            stop.send_keys(self.__query(final_month, final_year))
            self.__manual_click('DescargaZip')

            zip_exists = (len(self.DOWNLOADS_DIR) == 0)
            while not zip_exists:
                action = selenium.webdriver.ActionChains(self.DRIVER)
                action.pause(1)
                action.perform()
                action.reset_actions()
                if len(self.DOWNLOADS_DIR) != 0:
                    zip_exists = True
                    break

            for filename in os.listdir(self.DOWNLOADS_DIR):
                if filename.endswith(".zip"):
                    path = os.path.join(self.DOWNLOADS_DIR, filename)
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(self.DOWNLOADS_DIR)

            for filename in os.listdir(self.DOWNLOADS_DIR):
                if not filename.startswith("Generacion Liquidada_L0"):
                    os.remove(self.DOWNLOADS_DIR + '/' + filename)

        except selenium.common.exceptions.NoSuchElementException:
            raise

    def __data_point(self, date_time, value, production_type) -> dict:
        return {
            'ts': date_time,
            'value': float(value),
            'ba': 'CENACE',
            'meta': self.TRANSLATION_DICT[production_type] + ' (MWh)'
        }

    def scrape_month_range(self, initial_month: int, initial_year: int,
                           final_month: int, final_year: int):
        self.__retrieve_files(initial_month, initial_year,
                              final_month, final_year)

        data = []
        for filename in os.listdir(self.DOWNLOADS_DIR):
            if filename.endswith(".csv"):
                path = self.DOWNLOADS_DIR + '/' + filename
                df = pd.read_csv(path, skiprows=7)
                column_labels = list(df.columns)
                column_labels = column_labels[3:]

                for i in range(len(df)):
                    date = df.iloc[i, 1]
                    hour = str(df.iloc[i, 2] - 1).zfill(2)
                    date_time = arrow.get(
                        date + hour + ':00',
                        'DD/MM/YYYYHH:mm',
                        locale='es',
                        tzinfo='Mexico/General').datetime

                    for label in column_labels:
                        value = df.loc[i, label]
                        data.append(self.__data_point(
                            date_time, value, label.strip()))
        return data

    def scrape_month(self, month: int, year: int):
        return self.scrape_month_range(month, year, month, year)


def main():
    print("Initializing DRIVER...")
    mexico = Mexico()
    '''
    print("Scraping month/year range data...")
    data = mexico.scrape_month_range(10, 2020, 10, 2020)
    for dp in data:
        print(dp)
    '''
    print("Scraping specific month data...")
    data = mexico.scrape_month(10, 2020)
    for dp in data:
        print(dp)


if __name__ == "__main__":
    main()
