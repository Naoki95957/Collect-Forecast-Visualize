from abc import ABC, abstractmethod
# , ABCMeta
# from interface import implements, Interface


class ScraperAdapter(ABC):
    '''
        Serves an interface for abstraction for all our scrapers
    '''

    # @classmethod
    # def version(self): return "1.0"

    # def __init__(self):
    #     # raise NotImplementedError('The class cannot be instantiated')
    #     return None

    # will have latest scraped data
    # will be null so manager will look in database for last date
    # if not null, manager won't look in database
    # for last but just get last date

    @abstractmethod
    def set_last_scraped_date(self):
        '''
            The intention this is soley for real-time gathering

            This could alternatively be moved into a constructor:

            if there was downtime for multiple days, we might be able
            to call history but if there was downtime for only a few hours:
                - How would the adapter know what is 'new' or not?
                    - only the 'manager/main' would know:
                    - A setter would help instruct the last known scrape
        '''
        pass

    # filter data, remove BA and combine META in both functions
    @abstractmethod
    def scrape_history(
            self,
            start_year, start_month, start_day,
            end_year, end_month, end_day
            ) -> dict:
        '''
            Limit to history? Same all or as far back as we can? Cost to store?
            Lets start with 2 years for all countries if we can.
        '''
        # raise NotImplementedError("Must override abscract method 'scrape'!")
        pass

    # filter data, remove BA, factories, etc,
    # and combine production types in both functions
    # We want: TIME, VALUE, PRODUCTION TYPE
    # Thermal, Nuclear, Hydro, Wind, Solar

    '''
        scraper data : [{date, value, meta, ba}, ... ],

   Week or ANY time metric
            Time(Hr)


    Week
        Hour

    find doc: week
    find element in a doc: day

    [hour1, hour2, hour3]
    append hour4
    push [1, 2, 3, 4]

    given this structure:
        Week (doc)
            Day (array/dict/ whatever)
                Hour
                ...
                <can i insert here> without reading
            Day
                Hour
                ...

    Question:
    Is it possible to push data into these 'day' arrays without reading them?


    # this is an example that relies on using an append to the document
        realcollection.
            doc_<time by week>{
                extra info: "blahblah",
                entry_<DD/MM/YYYY-HH>:
                    [
                        {
                            value: x,
                            type: y //This would be the production type
                        },
                        {
                            value: x,
                            type: y
                        },
                        ...
                    ],
                entry_<time1>: [...],
                ...

            }
        predictedcollecton.
            doc_<time>{}
            ...
    '''
    @abstractmethod
    def scrape_new_data(self) -> dict:
        '''
            Check if data is in database first?(probably needs a
            setter since this shouldn't be directly handling the DB)
            Scrape any new data (data that hasn't been passed before
            and based on the landing page)

            The goal of this function is for real-time data as opposed
            to general data collection
        '''
        pass

    @abstractmethod
    def frequency(self) -> str:
        '''
        this would execute scrape_new_data only to get current landing page
        if downtime occurs, what is the solution? scrape_history? how to
        detect?

        manager(psudo name for main as of now) will check DB
        and determine missing info:
           - if missing:
                - scrape history(start of missing to (today - 1))
                - scrape_new_data
           - if not missing:
                - scrape_new_data
        '''
        pass
