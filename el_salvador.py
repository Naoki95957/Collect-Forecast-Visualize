import urllib
import json
import re
from bs4 import BeautifulSoup

URL = "http://estadistico.ut.com.sv/OperacionDiaria.aspx"

def opener() -> list:
    """
    Create a request to the URL defined above. This then takes the hidden keys 
    and event triggers to make a second request with the encoded data.

    The response is actually just encoded data to be loaded into the page.
    
    Luckily for us, it is encoded in JSON and is easily parsible.

    Returns an array of datapoints
    """
    opener = urllib.request.FancyURLopener()
    firstpage = opener.open(URL)
    soup = BeautifulSoup(firstpage, "html5lib")
    viewstate = soup.find_all("input", {"type": "hidden", "name": "__VIEWSTATE"})[0]['value']
    viewgenerator = soup.find_all("input", {"type": "hidden", "name": "__VIEWSTATEGENERATOR"})[0]['value']
    validation = soup.find_all("input", {"type": "hidden", "name": "__EVENTVALIDATION"})[0]['value']

    #this is our form data, largely observed by copying what the browser is doing via a packet sniffer
    formData = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': str(viewstate),
        '__VIEWSTATEGENERATOR': str(viewgenerator),
        'DXScript': '1_247,1_138,1_241,1_164,1_141,1_135,1_181,24_392,24_391,24_393,24_394,24_397,24_398,24_399,24_395,24_396,15_16,24_379,15_14,15_10,15_11,15_13',
        'DXCss': '1_28,1_29,24_359,24_364,24_360,15_0,15_4',
        '__CALLBACKID': 'ASPxDashboardViewer1',
        '__CALLBACKPARAM': 'c0:{"Task":"Initialize","DashboardId":"OperacionDiaria","Settings":{"calculateHiddenTotals":false},"RequestMarker":0,"ClientState":{}}',
        '__EVENTVALIDATION': str(validation),
    }

    #encode parameters to the URL
    encodedData = urllib.parse.urlencode(formData)
    encodedData = encodedData.encode('ascii')
    response = urllib.request.urlopen(URL, encodedData)
    
    #decode response
    responseContent = response.read()
    encoding = response.headers.get_content_charset('utf-8')
    responseTxt = responseContent.decode(encoding)

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

    #writing file to see it for now
    #file = open("output.txt", "w")
    #file.write(responseTxt)
    #file.close()

    #parse json and fetch our specific bits of data
    jsonObj = json.loads(responseTxt)
    data = jsonObj['PaneContent'][0]['ItemData']['DataStorageDTO']['Slices'][1]['Data']
    
    #the data is weird...
    #[x, y, z]:{"0":data}
    #x is column
    #y ???
    #z is row : by hour of day
    #data: the numbers we're after (MWh)
    #they don't even have their indexing correct!!!! :( 
    #the table goes: ... interconnection, solar, thermal
    #the index goes: ... interconnection, thermal, solar
    columnIdentifier = ["Biomass", "Geothermal", "HydroElectric", "Interconnection", "Thermal", "Solar"]
    for entry in data:
        column = int(re.search(r'\[(\d+),\d+,\d+\]', entry).group(1))
        row = int(re.search(r'\[\d+,\d+,(\d+)\]', entry).group(1))
        value = data[entry]["0"]
        print(entry,":\t\t", value)
        print("type:", columnIdentifier[column],"\nhour:", row, ":00", "\nvalue:", value, "MWh")

def formatter(columnName: str, hour: int, value: float) -> dict:
    """
    Takes column, hour, and value from the scraper and prepares it as a datapoint

    Should return a single dictionary in the proper form WattTime requested

    Parameters:

    columnName -- str that simple has the name of the production
    
    hour -- int that represents the hour in a 24hr day

    value -- a decimal value that represents the electricty produced in MWh
    """
    pass

def main():
    opener()

if __name__ == "__main__":
    main()
