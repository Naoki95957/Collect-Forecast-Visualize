

# TODO
"""
Is there audio in this?



"""


import urllib
import requests
from bs4 import BeautifulSoup
#import arrow # need arrow import?

URL = "http://estadistico.ut.com.sv/OperacionDiaria.aspx"

# TODO make this dictionary translate between spanish and english energy types
translation_dict = {
      'Spanish': 'English'
    }

# page.status_code == 200 # what is this??????


def translate(element):
    return translation_dict[element]


def get_scrape():
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html5lib') 
    
    viewstate = soup.find_all("input", {"type": "hidden", "name": "__VIEWSTATE"})
    eventvalidation = soup.find_all("input", {"type": "hidden", "name": "__EVENTVALIDATION"})
    viewstategenerator = soup.find_all("input", {"type": "hidden", "name": "__VIEWSTATEGENERATOR"})
    formData = (
        ("__VIEWSTATE", viewstate[0]['value']),
        ("__EVENTVALIDATION", eventvalidation[0]['value']),
        ("__VIEWSTATEGENERATOR", viewstategenerator[0]['value'])
    )
    #encode parameters to the URL w/ viewstate value
    #get new soup
    
    newpage = urllib.request.FancyURLopener(URL, urllib.parse.urlencode(formData))
    print(newpage, "newPage request above\n\n\n")
    #soup = BeautifulSoup(requests.get(URL + encodedFields).content, 'html5lib')
    return soup


def get_current_energies(soup: BeautifulSoup):
    return "todo"

    
 

    
    
    




def get_timestamp(soup):
    pass

    # Panama Example:
    #spanish_time = soup.find('div', {'class': 'sitr-update'}).find_all('span')[0].get_text()
    #time_stamp_sp = arrow.get(spanish_time, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    #time_stamp_en = time_stamp_sp.datetime.strftime("%Y-%-m-%-d %H:%M:%S")
    #return time_stamp_en


def get_unit_data(soup):
    pass
    #return unit_data


def main():
    soup = get_scrape()
    #print(soup.prettify())

    # Panama example:
    #current_energy_breakdown = get_current_energies(soup)
    #current_unit_data = get_unit_data(soup)
    #snapshot_time = get_timestamp(soup)



if __name__ == "__main__":
    main()
