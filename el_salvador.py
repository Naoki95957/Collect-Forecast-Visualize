import requests
import json
import datetime
import arrow
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup


class ElSalvador:

    URL = 'http://estadistico.ut.com.sv/OperacionDiaria.aspx'
    FREQUENCY = 'hourly'
    BA = 'Unidad de Transacciones'

    def scrape_data(self) -> list:
        """
        Grabs the daily report for El Salvador.

        Return: list of datapoints
        """
        page = self.__get_data_page()
        json_obj = json.loads(page)
        table = json_obj['PaneContent'][0]['ItemData']
        table = table['DataStorageDTO']['Slices'][1]['Data']
        current_day = json_obj['DashboardParameters'][0]
        current_day = current_day['Values'][0]['DisplayText']
        current_day = re.sub(' 12:00:00 a.m.', '', current_day)

        column_labels = [
            'Biomass',
            'Geothermal',
            'HydroElectric',
            'Interconnection',
            'Thermal',
            'Solar']
        data = []
        for i in table:
            hour = re.search(r'\[\d+,\d+,(\d+)\]', i).group(1)
            date = arrow.get(
                current_day + hour.zfill(2) + ':00',
                'DD/MM/YYYYHH:mm',
                locale='es',
                tzinfo='America/El_Salvador').datetime
            value = table[i]['0']
            column_index = int(re.search(r'\[(\d+),\d+,\d+\]', i).group(1))
            production_type = column_labels[column_index]
            data_point = self.__data_point(date, value, production_type)
            data.append(data_point)
        return data

    def __get_data_page(self) -> str:
        """
        Grabs the data page. To do this it must first send an initial
        request for the page. Then it retrieves the form data and uses
        it to send a second request. Finally it decodes the page and
        reformats it for parsing.

        Return: decoded data page in .json format
        """
        initial_page = requests.get(self.URL)
        soup = BeautifulSoup(initial_page.content, 'html.parser')

        form_data = self.__get_form_data(soup)
        encoded_data = urlencode(form_data).encode('ascii')
        response = urlopen(self.URL, encoded_data)

        encoding = response.headers.get_content_charset('utf-8')
        page = response.read().decode(encoding)
        page = page.replace("\\t", "\t")
        page = page.replace("\\n", "\n")
        page = page.replace("\\'", "'")
        page = page.replace("\'", "\"")
        page = page.split('\n', 1)[1]
        page = page[:page.rfind('\n')]
        page = "{" + page + "}"
        page = re.sub(r'(new Date\((\d+,)+\d\))', '\"some date\"', page)
        return page

    def __get_form_data(self, soup: BeautifulSoup) -> dict:
        hidden_fields = soup.find_all('input', type='hidden')
        return {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hidden_fields[0]['value'],
            '__VIEWSTATEGENERATOR': hidden_fields[1]['value'],
            'DXScript': (
                '1_247,1_138,1_241,1_164,1_141,1_135,1_181,24_392,'
                '24_391,24_393,24_394,24_397,24_398,24_399,24_395,'
                '24_396,15_16,24_379,15_14,15_10,15_11,15_13'),
            'DXCss': '1_28,1_29,24_359,24_364,24_360,15_0,15_4',
            '__CALLBACKID': 'ASPxDashboardViewer1',
            '__CALLBACKPARAM': (
                'c0:{"Task":"Initialize","DashboardId":"OperacionDiaria",'
                '"Settings":{"calculateHiddenTotals":false},"RequestMarker":0,'
                '"ClientState":{}}'),
            '__EVENTVALIDATION': hidden_fields[2]['value']
        }

    def __data_point(self, date, value, production_type) -> dict:
        """
        Parameters:
            date -- datetime object for datapoint (realative timezone)
            value -- float value of electricity production in MWh
            production_type -- string that contains the production type

        Return: dictionary (format defined by WattTime)
        """
        return {
            'ts': date,
            'value': value,
            'ba': self.BA,
            'meta': production_type + ' (MWh)'
        }


def main():
    scraper = ElSalvador()
    for datapoint in scraper.scrape_data():
        print(datapoint)


if __name__ == "__main__":
    main()
