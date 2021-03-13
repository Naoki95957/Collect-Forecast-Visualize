import datetime
import arrow

# the basis to check the db
doc_start_time = datetime.datetime(year=2016, month=12, day=27)

def str2datetime(string: str, tzinfo=None) -> datetime.datetime:
    '''
    This str to datetime is for the hourly format we're using
    '''
    return arrow.get(string, "HH-DD/MM/YYYY", tzinfo=tzinfo)

def get_doc(date: datetime.datetime) -> str:
    '''
    Helper function to get the doc for x/y/z date

    returns the str that should be the ID of the doc
    '''
    # yes this is a bit redundant, but I wanna have JUST days, not hours
    end = datetime.datetime(date.year, date.month, date.day)
    diff = (end - doc_start_time).days % 7
    week = end - datetime.timedelta(days=diff)
    week_date = arrow.Arrow.strptime(str(week), "%Y-%m-%d %H:%M:%S").datetime
    return week_date.strftime("%d/%m/%Y")