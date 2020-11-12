import requests
import dateutil
import json
import datetime
import arrow
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup

class ElSalvador:

    URL = "http://estadistico.ut.com.sv/OperacionDiaria.aspx"
    FREQUENCY: 'hourly'
    BA = "Unidad de Transacciones"
    META = [
        "Biomass", 
        "Geothermal", 
        "HydroElectric", 
        "Interconnection", 
        "Thermal", 
        "Solar"
    ]


    def scrape_data(self) -> list:
        """
        Grabs the daily report for El Salvador.

        Return: list of datapoints
        """
        page = self.__get_data_page()
        jsonObj = json.loads(page)
        data = jsonObj['PaneContent'][0]['ItemData']['DataStorageDTO']['Slices'][1]['Data']
        currentDay = jsonObj['DashboardParameters'][0]['Values'][0]['DisplayText']
        currentDay = re.sub(" 12:00:00 a.m.", "", currentDay)

        listOfDatapoints = []
        for entry in data:
            column = int(re.search(r'\[(\d+),\d+,\d+\]', entry).group(1))
            row = re.search(r'\[\d+,\d+,(\d+)\]', entry).group(1)
            value = data[entry]["0"]
            hour = row.zfill(2) + ":00"
            date = arrow.get(
                currentDay + hour,
                'DD/MM/YYYYHH:mm',
                locale="es", 
                tzinfo=dateutil.tz.gettz('America/El_Salvador')
            ).datetime
            datapoint = self.__formatter(self.META[column], date, value)
            listOfDatapoints.append(datapoint)
        return listOfDatapoints


    def __get_data_page(self) -> str:
        """
        Grabs the data page. To do this it must first send an initial request
        for the page. Then it retrieves the form data and uses it to send a second
        request. Finally it decodes the page and reformats it for parsing.

        Return: decoded data page in .json format
        """
        firstpage = requests.get(self.URL)
        soup = BeautifulSoup(firstpage.content, "html5lib")

        formData = self.__getFormData(soup)
        encodedData = urlencode(formData).encode('ascii')
        response = urlopen(self.URL, encodedData)

        decoding = response.headers.get_content_charset('utf-8')
        page = response.read().decode(decoding)
        page = page.replace("\\t", "\t")
        page = page.replace("\\n", "\n")
        page = page.replace("\\'", "'")
        page = page.replace("\'", "\"")
        page = page.split('\n', 1)[1]
        page = page[:page.rfind('\n')]
        page = "{" + page + "}"
        page = re.sub(r'(new Date\((\d+,)+\d\))', '\"some date\"', page)
        return page


    def __getFormData(self, soup: BeautifulSoup) -> dict:
        hiddenFields = soup.find_all("input", type="hidden")
        return {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': hiddenFields[0]['value'],
            '__VIEWSTATEGENERATOR': hiddenFields[1]['value'],
            'DXScript': (
                '1_247,1_138,1_241,1_164,1_141,1_135,1_181,24_392,'
                '24_391,24_393,24_394,24_397,24_398,24_399,24_395,'
                '24_396,15_16,24_379,15_14,15_10,15_11,15_13'
            ),
            'DXCss': '1_28,1_29,24_359,24_364,24_360,15_0,15_4',
            '__CALLBACKID': 'ASPxDashboardViewer1',
            '__CALLBACKPARAM': (
                'c0:{"Task":"Initialize","DashboardId":"OperacionDiaria",'
                '"Settings":{"calculateHiddenTotals":false},"RequestMarker":0,'
                '"ClientState":{}}'
            ),
            '__EVENTVALIDATION': hiddenFields[2]['value']
        }

    def __formatter(
        self,
        columnName: str,
        dateTime: datetime.date,
        value: float
    ) -> dict:
        '''
        Parameters:
            columnName -- string that contains the type of production (meta)
            dateTime -- timestamp for datapoint (realative timezone)
            value -- decimal value of electricity production in MWh

        Return: dictionary (format defined by WattTime)
        '''
        return {
            'ts': dateTime,
            'value': value,
            'ba': self.BA,
            'meta': columnName + " (MWh)"
        }

def main():
    scraper = ElSalvador()
    for datapoint in scraper.scrape_data():
        print(datapoint)

if __name__ == "__main__":
    main()
