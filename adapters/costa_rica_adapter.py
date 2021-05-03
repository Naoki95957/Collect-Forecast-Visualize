import datetime
import pandas as pd
from scrapers.costa_rica import CostaRica
from adapters.scraper_adapter import ScraperAdapter

"""
This class has the scraper_adaptor interface which need to be implemented here.
The purpose of this class is to filter the data and put it into different data.
This class also checks when to get that data
The manager class uses this class
"""


class CostaRicaAdapter(ScraperAdapter):
    __frequency = 60 * 60 * 24
    PLANT_DICTIONARY = {
        'Arenal': 'Hydroelectric',
        'Angostura': 'Hydroelectric',
        'Balsa Inferior': 'Hydroelectric',
        'Barro Morado': 'Hydroelectric',
        'Bijagua': 'Hydroelectric',
        'Birris12': 'Hydroelectric',
        'Birris3': 'Hydroelectric',
        'Cachí': 'Hydroelectric',
        'Canalete': 'Hydroelectric',
        'Caño Grande': 'Hydroelectric',
        'Caño Grande III': 'Hydroelectric',
        'Chocosuelas': 'Hydroelectric',
        'Chucás': 'Hydroelectric',
        'Daniel Gutiérrez': 'Hydroelectric',
        'Dengo': 'Hydroelectric',
        'Don Pedro': 'Hydroelectric',
        'Doña Julia': 'Hydroelectric',
        'El Embalse': 'Hydroelectric',
        'Garita': 'Hydroelectric',
        'La Joya': 'Hydroelectric',
        'Los Negros': 'Hydroelectric',
        'Los Negros II': 'Hydroelectric',
        'Peñas Blancas': 'Hydroelectric',
        'Pirrís': 'Hydroelectric',
        'Poás I y II': 'Hydroelectric',
        'Reventazón': 'Hydroelectric',
        'Río Lajas': 'Hydroelectric',
        'Río Macho': 'Hydroelectric',
        'Río Segundo II': 'Hydroelectric',
        'San Lorenzo (C)': 'Hydroelectric',
        'Sandillal': 'Hydroelectric',
        'Santa Rufina': 'Hydroelectric',
        'Torito': 'Hydroelectric',
        'Toro I': 'Hydroelectric',
        'Toro II': 'Hydroelectric',
        'Toro III': 'Hydroelectric',
        'Tuis (JASEC)': 'Hydroelectric',
        'Ventanas-Garita': 'Hydroelectric',
        'Cariblanco': 'Hydroelectric',
        'Cubujuquí': 'Hydroelectric',
        'Echandi': 'Hydroelectric',
        'Volcán': 'Hydroelectric',
        'CNFL': 'Hydroelectric',
        'Guápiles': 'Hydroelectric',
        'Hidrozarcas': 'Hydroelectric',
        'Matamoros': 'Hydroelectric',
        'MOVASA': 'Hydroelectric',
        'Orotina': 'Hydroelectric',
        'Platanar': 'Hydroelectric',
        'Pocosol': 'Hydroelectric',
        'Rebeca I': 'Hydroelectric',
        'Suerkata': 'Hydroelectric',
        'Tacares': 'Hydroelectric',
        'Tapezco': 'Hydroelectric',
        'Vara Blanca': 'Hydroelectric',
        'El General': 'Hydroelectric',
        'Garabito': 'Thermal',
        'Moín II': 'Thermal',
        'Moín III': 'Thermal',
        'Las Pailas I': 'Geothermal',
        'Las Pailas II': 'Geothermal',
        'Miravalles I': 'Geothermal',
        'Miravalles II': 'Geothermal',
        'Miravalles III': 'Geothermal',
        'Miravalles V': 'Geothermal',
        'Boca de Pozo': 'Geothermal',
        'Pailas': 'Geothermal',
        'Jorge Manuel Dengo': 'Geothermal',
        'Altamira': 'Wind',
        'Campos Azules': 'Wind',
        'Chiripa': 'Wind',
        'Los Santos': 'Wind',
        'Orosí': 'Wind',
        'Plantas Eólicas': 'Wind',
        'Tejona': 'Wind',
        'Tilawind': 'Wind',
        'Vientos de La Perla': 'Wind',
        'Vientos de Miramar': 'Wind',
        'Vientos del Este': 'Wind',
        'Aeroenergía': 'Wind',
        'PE Cacao': 'Wind',
        'PE Mogote': 'Wind',
        'PE Río Naranjo': 'Wind',
        'PEG': 'Wind',
        'Taboga': 'Wind',
        'Valle Central': 'Wind',
        'Intercambio Norte': 'Interchange',
        'Intercambio Sur': 'Interchange',
        'El Angel': 'Other',
        'El Angel Ampliación': 'Other',
        'El Viejo': 'Other',
        'Otros': 'Other',
        'Carrillos': 'Solar',
        'Parque Solar Juanilama': 'Solar',
        'Parque Solar Miravalles': 'Solar',
        'La Esperanza (CoopeL)': 'Solar',
        'Other' : 'Other'
    }

    PLANT_DEFINITIONS = [
        'Hydroelectric',
        'Geothermal',
        'Thermal',
        'Wind',
        'Interchange',
        'Solar',
        'Other'
    ]

    historic_data = None
    appended_hist = None
    new_data = None
    appended_new = None
    last_scrape_date = None
    last_scrape_list = []

    def __init__(self):
        self.scraper = CostaRica()

    def set_last_scraped_date(self, date: datetime.datetime):
        self.last_scrape_list = None
        self.last_scrape_date = date

    def scrape_history(self, start_year, start_month, start_day, end_year, end_month, end_day) -> dict:
        self.historic_data = self.scraper.date_range(start_year, start_month, start_day, end_year, end_month, end_day)

        self.appended_hist = pd.DataFrame(self.historic_data)
        self.appended_hist = self.appended_hist.drop('ba', axis=1)
        self.appended_hist['meta'] = self.appended_hist['meta'].replace(self.PLANT_DICTIONARY)
        self.appended_hist = self.appended_hist.groupby(['ts', 'meta'])['value'].agg('sum').reset_index()

        return self.__filter_data(self.appended_hist)

    def scrape_new_data(self) -> dict:
        will_scrape = False
        if not self.last_scrape_date:
            will_scrape = True
        else:
            delta = datetime.datetime.now() - datetime.timedelta(1) - self.last_scrape_date
            if delta.days > 0:
                will_scrape = True
            if delta.seconds / self.__frequency > 1:
                will_scrape = True

        if will_scrape:
            self.last_scrape_date = datetime.datetime.now() - datetime.timedelta(1)
            year = self.last_scrape_date.year
            month = self.last_scrape_date.month
            day = self.last_scrape_date.day
            self.new_data = self.scraper.date(year, month, day)

            self.appended_new = pd.DataFrame(self.new_data)
            self.appended_new = self.appended_new.drop('ba', axis=1)
            self.appended_new['meta'] = self.appended_new['meta'].replace(self.PLANT_DICTIONARY)
            self.appended_new = self.appended_new.groupby(['ts', 'meta'])['value'].agg('sum').reset_index()

            return self.__filter_data(self.appended_new)

    def __filter_data(self, data) -> dict:
        buffer = dict()
        for i in range(0, len(data) - 1):
            time = data.iat[i, 0].strftime("%H-%d/%m/%Y")
            if time in buffer:
                continue
            entries = list()
            for j in range(i, len(data) - 1):
                if (
                        data.iat[j, 0] == data.iat[i, 0] and
                        not data.iat[i, 1] == data.iat[j, 1]
                    ):
                    dict_val = dict()
                    dict_val['value'] = data.iat[j, 2]
                    prod_type = data.iat[j, 1]
                    if prod_type not in self.PLANT_DEFINITIONS:
                        prod_type = 'Other'
                    dict_val['type'] = prod_type
                    entries.append(dict_val)
            buffer[time] = entries
        return buffer

    def frequency(self) -> int:
        return self.__frequency


def main():
    ca = CostaRicaAdapter()

    start_year = 2020
    start_month = 11
    start_day = 1
    end_year = 2021
    end_month = 1
    end_day = 24

    data = ca.scrape_history(start_year, start_month, start_day, end_year, end_month, end_day)
    # data = ca.scrape_new_data()
    for each in data:
        print(each, data[each], "\n")


if __name__ == "__main__":
    main()
