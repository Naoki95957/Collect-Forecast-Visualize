import datetime
import platform
import re
from pathlib import Path
import os
import arrow
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

import pandas as pd


class Sun:
    URL = 'https://www.timeanddate.com/sun/el-salvador/san-salvador'
    driver = None

    def __init__(self):
        options = Options()
        options.headless = True
        operating_system = platform.system()
        full_path = str(Path(str(__file__)).parents[0])
        chrome_driver = '/drivers/mac_chromedriver88'
        if operating_system == "Linux":
            architecture = platform.architecture()[0]
            if architecture == '32bit':
                chrome_driver = '/drivers/linux_chromedriver65_32bit'
            else:
                chrome_driver = '/drivers/linux_chromedriver87_64bit'
            os.chmod(full_path + chrome_driver, 0o777)
        elif operating_system == "Windows":
            chrome_driver = '/drivers/win_chromedriver88.exe'
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + chrome_driver))
        self.driver.get(self.URL)

    def __del__(self):
        self.driver.quit()
    
    def scrape(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        data = []
        table = soup.find('table', attrs={'id':'as-monthsun'})
        table_body = table.find('tbody')

        rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append(cols)
            
        print(pd.DataFrame(data))


    # def date(self, year, month, day) -> list:
    #     return self.date_range(year, month, day, year, month, day)

    # def date_range(self, start_year, start_month, start_day,
    #                end_year, end_month, end_day) -> list:
    #     start_date = datetime.date(start_year, start_month, start_day)
    #     end_date = datetime.date(end_year, end_month, end_day)
    #     all_data_points = []
    #     while start_date <= end_date:
    #         # Reformat date to match costa rica's search field
    #         date = (str(start_date.day).zfill(2) + "/" +
    #                 str(start_date.month).zfill(2) + "/" +
    #                 str(start_date.year).zfill(4))
    #         search_date_field = self.driver.find_element_by_name(
    #             "formPosdespacho:txtFechaInicio_input")
    #         search_date_field.clear()
    #         search_date_field.send_keys(date + Keys.RETURN)
    #         all_data_points.extend(self.__scrape_data(date))
    #         start_date += datetime.timedelta(days=1)
    #     return all_data_points

    # def __scrape_data(self, date) -> list:
    #     soup = BeautifulSoup(self.driver.page_source, "html.parser")
    #     plants_hours = soup.find('tbody', {
    #         'id': 'formPosdespacho:j_id_1a_data'}).find_all('span')
    #     date_data_points = []
    #     for plant_hour in plants_hours:
    #         if (plant_hour.has_attr('title') and bool(plant_hour.getText())
    #                 and 'Total' not in plant_hour['title']):
    #             date_data_points.append(self.__data_point(date, plant_hour))
    #     return date_data_points

    # def __data_point(self, date, plant_hour) -> dict:
    #     plant = re.search(r'(.*?),(.*)', plant_hour['title']).group(1)
    #     emission_hour = re.search(r'(.*?),(.*)', plant_hour['title']).group(2)
    #     time_stamp = arrow.get(
    #         date + emission_hour,
    #         'DD/MM/YYYY HH:mm',
    #         locale="es",
    #         tzinfo='America/Costa_Rica').datetime
    #     return {'ts': time_stamp,
    #             'value': float(plant_hour.getText()),
    #             'ba': 'Operación Sistema Eléctrico Nacional',
    #             'meta': plant}


def main():
    print("Initializing driver...")
    sun = Sun()

    print('Scraping...')
    sun.scrape()


if __name__ == "__main__":
    main()
