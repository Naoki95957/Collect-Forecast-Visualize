import urllib
from bs4 import BeautifulSoup

URL = "http://estadistico.ut.com.sv/OperacionDiaria.aspx"

def opener():
    """
    So this makes the initial request, then submits the form data to get the appropriate response from the server

    From here there needs to be some sort of loading going on.
    The packet still doesn't contain a matching html page to that of a browser for example
    But we are making the same GET/POST to get the appropriate data. Its just hiding in here somewhere
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
    soup = BeautifulSoup(response, "html5lib")
    return soup

def main():
    soup = opener()

if __name__ == "__main__":
    main()