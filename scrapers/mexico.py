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
    """
    This class scrapes the energy generation data from the files
    provided in the url. The website reports the data for an entire
    month at a time, thus it does not have data for the current
    month. It may take up to 2 weeks into the following month to
    to provide new data. It reports data by the day and the hour
    (24 hours per day). The data only dates back to April of 2016
    To retrieve data run the scrape_month_range or scrape_month,
    for a range or single month of data.
    """
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
    driver = None
    directory = ''
    downloads_dir = ''

    def __init__(self):
        self.directory = os.getcwd()
        if not self.directory.endswith('scrapers'):
            self.directory = os.path.join(self.directory, 'scrapers')
        drivers_dir = os.path.join(self.directory, 'drivers')
        self.downloads_dir = os.path.join(self.directory, 'mexico_downloads')
        try:
            os.mkdir(self.downloads_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                os.remove(self.downloads_dir)
                os.mkdir(self.downloads_dir)

        options = Options()
        options.headless = True
        prefs = {"download.default_directory": self.downloads_dir}
        options.add_experimental_option("prefs", prefs)

        operating_system = platform.system()
        chrome_driver = 'mac_chromedriver86'
        if operating_system == "Linux":
            architecture = platform.architecture()[0]
            if architecture == '32bit':
                chrome_driver = 'linux_chromedriver65_32bit'
            else:
                chrome_driver = 'linux_chromedriver86_64bit'
            os.chmod(os.path.join(drivers_dir, chrome_driver), 0o777)
        elif operating_system == "Windows":
            chrome_driver = 'win_chromedriver86.exe'

        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(os.path.join(drivers_dir, chrome_driver))
        )
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()
        shutil.rmtree(self.downloads_dir)

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

    def __retrieve_files(self, initial_month: int, initial_year: int,
                         final_month: int, final_year: int):
        try:
            start = self.driver.find_element_by_id(
                "ctl00_ContentPlaceHolder1_FechaInicial_dateInput")
            start.clear()
            start.send_keys(self.__query(initial_month, initial_year))
            stop = self.driver.find_element_by_id(
                "ctl00_ContentPlaceHolder1_FechaFinal_dateInput")
            stop.clear()
            stop.send_keys(self.__query(final_month, final_year))
            self.__manual_click('DescargaZip')

            zip_exists = False
            i = 0
            while not zip_exists:
                action = selenium.webdriver.ActionChains(self.driver)
                action.pause(1)
                action.perform()
                action.reset_actions()
                for filename in os.listdir(self.downloads_dir):
                    if filename.endswith('.zip'):
                        zip_exists = True
                        break
                if i == 180:
                    raise Exception('File unable to download')

            for filename in os.listdir(self.downloads_dir):
                if filename.endswith(".zip"):
                    path = os.path.join(self.downloads_dir, filename)
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(self.downloads_dir)

            for filename in os.listdir(self.downloads_dir):
                if not filename.startswith("Generacion Liquidada_L0"):
                    os.remove(self.downloads_dir + '/' + filename)

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
        """
        The mexico data provided is in whole month chunks.
        Any new month data won't be provided until up to 2
        weeks into the following month. scrape_month_range
        provides data across the input month range.
        The data only dates back to April of 2016.
        """
        self.__retrieve_files(initial_month, initial_year,
                              final_month, final_year)

        data = []
        for filename in os.listdir(self.downloads_dir):
            if filename.endswith(".csv"):
                path = self.downloads_dir + '/' + filename
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
        """
        The mexico data provided is in whole month chunks.
        Any new month data won't be provided until up to 2
        weeks into the following month. scrape_month provides
        data for a single month of input.
        The data only dates back to April of 2016.
        """
        return self.scrape_month_range(month, year, month, year)


def main():
    print("Initializing driver...")
    mexico = Mexico()

    print("Scraping month/year range data...")
    data = mexico.scrape_month_range(1, 2020, 10, 2020)
    for dp in data:
        print(dp)
    '''
    print("Scraping specific month data...")
    data = mexico.scrape_month(10, 2020)
    for dp in data:
        print(dp)
    '''


if __name__ == "__main__":
    main()
