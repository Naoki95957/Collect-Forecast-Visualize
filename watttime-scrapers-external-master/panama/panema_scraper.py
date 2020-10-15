import requests
from bs4 import BeautifulSoup
import arrow

translation_dict = {
      'Hídrica': 'hydro',
      'Eólica': 'wind',
      'Solar': 'solar',
      'Biogas': 'biomass',
      'Térmica': 'thermal'
    }

# page.status_code == 200


def translate(element):
    return translation_dict[element]


def get_scrape():
    page = requests.get("http://sitr.cnd.com.pa/m/pub/gen.html")
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup


def get_current_energies(soup):
    current_energies = []
    table_elements = soup.find('table', {'class': 'sitr-pie-layout'}).find_all('span')
    for element in table_elements:
        element_str = element.get_text()
        energy_type = translate(element_str.split()[0])
        energy = element_str.split()[1]
        current_energies.append({energy_type: energy})
    return current_energies


def get_timestamp(soup):
    spanish_time = soup.find('div', {'class': 'sitr-update'}).find_all('span')[0].get_text()
    time_stamp_sp = arrow.get(spanish_time, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    time_stamp_en = time_stamp_sp.datetime.strftime("%Y-%-m-%-d %H:%M:%S")
    return time_stamp_en


def get_unit_data(soup):
    unit_data = []
    table_elements = soup.find_all('table', {'class': 'sitr-table-gen'})
    thermal_table = table_elements[1].find_all("span")
    for i, element in enumerate(thermal_table):
        if i == 0:
            continue
        element_str = element.get_text()
        if i < (len(thermal_table) - 1) and i % 2 != 0:
            corresponding_data = thermal_table[i+1].get_text()
            unit_data.append({element_str: int(float(corresponding_data))})
    return unit_data


def main():
    soup = get_scrape()
    current_energy_breakdown = get_current_energies(soup)
    current_unit_data = get_unit_data(soup)
    snapshot_time = get_timestamp(soup)

    print(current_energy_breakdown)
    print(current_unit_data)
    print(snapshot_time)


if __name__ == "__main__":
    main()
