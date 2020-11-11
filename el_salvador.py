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
    TIME_ZONE = dateutil.tz.gettz('America/El_Salvador')
    BA = "Unidad de Transacciones"
    META = [
        "Biomass", 
        "Geothermal", 
        "HydroElectric", 
        "Interconnection", 
        "Thermal", 
        "Solar"
    ]

    def scrape(self) -> list:
        """
        Create a request to the URL defined above. This then takes the hidden keys 
        and event triggers to make a second request with the encoded data.

        The response is actually just encoded data to be loaded into the page.
        
        Luckily for us, it is encoded in JSON and is easily parsible.

        Returns an array of datapoints
        """
        firstpage = requests.get(self.URL)
        soup = BeautifulSoup(firstpage.content, "html5lib")
        formData = self.getFormData(soup)

        encodedData = urlencode(formData).encode('ascii')
        response = urlopen(self.URL, encodedData)
        decoding = response.headers.get_content_charset('utf-8')
        responseTxt = response.read().decode(decoding)

        #had to do manual replacing since decoding it doesn't completely work ^^
        responseTxt = responseTxt.replace("\\t", "\t")
        responseTxt = responseTxt.replace("\\n", "\n")
        responseTxt = responseTxt.replace("\\'", "'")
        responseTxt = responseTxt.replace("\'", "\"")
        #cleans up the junk in the response to get just the JSON part
        responseTxt = responseTxt.split('\n', 1)[1]
        responseTxt = responseTxt[:responseTxt.rfind('\n')]
        responseTxt = "{" + responseTxt + "}"
        #yes, this monster is back but because python can't perfectly parse JSON. So 'new Date' is now instead a string
        responseTxt = re.sub(r'(new Date\((\d+,)+\d\))', '\"some date\"', responseTxt)

        #parse json and fetch our specific bits of data
        jsonObj = json.loads(responseTxt)
        #table data
        data = jsonObj['PaneContent'][0]['ItemData']['DataStorageDTO']['Slices'][1]['Data']
        #current day
        currentDay = jsonObj['DashboardParameters'][0]['Values'][0]['DisplayText']
        currentDay = re.sub(" 12:00:00 a.m.", "", currentDay)

        #the data is weird...
        #[x, y, z]:{"0":data}
        #x is column
        #y ???
        #z is row : by hour of day
        #data: the numbers we're after (MWh)
        #they don't even have their indexing correct!!!! :( 
        #the table goes: ... interconnection, solar, thermal
        #the index goes: ... interconnection, thermal, solar
        listOfDatapoints = []
        for entry in data:
            column = int(re.search(r'\[(\d+),\d+,\d+\]', entry).group(1))
            row = re.search(r'\[\d+,\d+,(\d+)\]', entry).group(1)
            value = data[entry]["0"]
            hour = row.zfill(2) + ":00"
            date = arrow.get(currentDay + hour, 'DD/MM/YYYYHH:mm', locale="es", tzinfo=self.TIME_ZONE).datetime
            datapoint = self.formatter(self.META[column], date, value)
            listOfDatapoints.append(datapoint)
        return listOfDatapoints

    def getFormData(self, soup: BeautifulSoup) -> dict:
        hiddenFields = soup.find_all("input", type="hidden")

        viewState = hiddenFields[0]['value']
        viewStateGenerator = hiddenFields[1]['value']
        dxScript = (
            '1_247,1_138,1_241,1_164,1_141,1_135,1_181,24_392,'
            '24_391,24_393,24_394,24_397,24_398,24_399,24_395,'
            '24_396,15_16,24_379,15_14,15_10,15_11,15_13'
        )
        dxCss = '1_28,1_29,24_359,24_364,24_360,15_0,15_4'
        callBackId = 'ASPxDashboardViewer1'
        callBackParam = (
            'c0:{"Task":"Initialize","DashboardId":"OperacionDiaria",'
            '"Settings":{"calculateHiddenTotals":false},"RequestMarker":0,'
            '"ClientState":{}}'
        )
        eventValidation = hiddenFields[2]['value']

        # this is our form data, largely observed by copying what the browser is doing via a packet sniffer
        return {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewState,
            '__VIEWSTATEGENERATOR': viewStateGenerator,
            'DXScript': dxScript,
            'DXCss': dxCss,
            '__CALLBACKID': callBackId,
            '__CALLBACKPARAM': callBackParam,
            '__EVENTVALIDATION': eventValidation
        }

    def formatter(self, columnName: str, dateTime: datetime.date, value: float) -> dict:
        """
        Takes column, hour, and value from the scraper and prepares it as a datapoint

        The day should always be the current day and El-Salvador's time zone is:
        Central Standard Time (GMT-6)

        Their reports show up an hour late.

        Should return a single dictionary in the proper form WattTime requested

        Parameters:

        columnName -- str that simple has the name of the production
        
        hour -- int that represents the hour in a 24hr day

        value -- a decimal value that represents the electricty produced in MWh
        """
        #datapoint1 = 
        #{
        #    'ts': <timezone aware datetime object>,
        #    'value': <value of grid parameter (type float or int)>,
        #    'ba': <string specifying balancing authority or subregion eg 'PJM_WEST', 'NL' for Netherlands, 'ISONE_VERMONT'>,
        #    'meta': <optional field specifying fuel type (if generation) or other information needed to make sense of the particular data point>
        #}
        # So the returned data looks something like: [datapoint1, datapoint2, datapoint3 ....]
        # Our BA is: Unidad de Transacciones (UT)
        # Transactions Unit (Unidad de Transacciones)

        datapoint = {}
        datapoint['ts'] = dateTime
        datapoint['value'] = value
        datapoint['ba'] = self.BA
        datapoint['meta'] = columnName + " (MWh)"
        return datapoint

def main():
    scraper = ElSalvador()
    for datapoint in scraper.scrape():
        print(datapoint)

if __name__ == "__main__":
    main()
