

# TODO
"""




"""



import requests
from bs4 import BeautifulSoup
#import arrow # need arrow import?

translation_dict = {
      'Spanish': 'English'
    }

# page.status_code == 200 # what is this??????


def translate(element):
    return translation_dict[element]


def get_scrape():
    """

    """

    # Panama example:
    #page = requests.get("http://sitr.cnd.com.pa/m/pub/gen.html")
    #soup = BeautifulSoup(page.content, 'html.parser')
    return soup


def get_current_energies(soup):


    # Panama Example:
    #current_energies = []
    #table_elements = soup.find('table', {'class': 'sitr-pie-layout'}).find_all('span')
    #for element in table_elements:
     #  energy_type = translate(element_str.split()[0])
     #   energy = element_str.split()[1]
     #   current_energies.append({energy_type: energy})
    return current_energies


def get_timestamp(soup):


    # Panama Example:
    #spanish_time = soup.find('div', {'class': 'sitr-update'}).find_all('span')[0].get_text()
    #time_stamp_sp = arrow.get(spanish_time, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    #time_stamp_en = time_stamp_sp.datetime.strftime("%Y-%-m-%-d %H:%M:%S")
    return time_stamp_en


def get_unit_data(soup):
    pass
    return unit_data


def main():
    soup = get_scrape()


    # Panama example:
    #current_energy_breakdown = get_current_energies(soup)
    #current_unit_data = get_unit_data(soup)
    #snapshot_time = get_timestamp(soup)



if __name__ == "__main__":
    main()
