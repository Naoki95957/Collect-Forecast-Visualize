# Standard
from bisect import bisect_left
import datetime
import argparse

# Scientific
import pandas as pd


def get_date(df):
    """
    gets the data from the dataframe
    Parameters
    ----------
    df: DataFrame
        original data frame

    Returns
    -------
    date: string
        the date that the CSV is from, in form DD/MM/YYYY

    """
    full_text = df.iloc[1]['station']
    return full_text[-10:]


def get_desired_index(desired_list, current_index):
    """
    gets the desired number in a list of numbers when given a number. The desired number is the one which is the
    closest lower number in the lsit.
    Parameters
    ----------
    desired_list: :obj:`list` of :obj:`int`
        list you want to check against. This list contains the indexes of a variable.
    current_index: int
        the number you currently have

    Returns
    -------
    int
        the index of the list where the corresponding number is.

    """
    return bisect_left(desired_list, current_index) - 1


def get_region_locations(df):
    """
    given the original dataframe, this function gets a list of the region names and the rows they appear on.
    Parameters
    ----------
    df: DataFrame
        original dataframe.

    Returns
    -------
    region_names: :obj:`list` of :obj:`str`
        a list of the region names
    region_title_locations: :obj:`list` of :obj:`int`
        the row number where each region name occurs in the dataframe
    """
    region_markers = df.loc[df['station'] == "REGION TOTAL"].index.values.tolist()
    # region_title_locations = numpy.array(region_markers) -1
    region_title_locations = [mark - 1 for mark in region_markers]
    region_names = []
    for region_title_location in region_title_locations:
        region_names.append(df.iloc[region_title_location]['station'])
    return region_names, region_title_locations


def get_state_locations(df):
    """
    given the original dataframe, this function gets a list of the state names and the rows they appear on.
    Parameters
    ----------
    df: DataFrame
        original dataframe.

    Returns
    -------
    :obj:`list` of :obj:`str`
        state_names: a list of the state names
    :obj:`list` of :obj:`int`
        state_title_locations: the row number where each state name occurs in the dataframe
    """
    state_markers = df.loc[df['station'] == "STATE TOTAL"].index.values.tolist()
    state_title_locations = [mark - 1 for mark in state_markers]
    state_names = []
    for state_title_location in state_title_locations:
        state_names.append(df.iloc[state_title_location]['station'])
    return state_names, state_title_locations


def get_sector_locations(df):
    """
    given the original dataframe, this function gets a list of the sector names and the rows they appear on.
    Note this allows duplicates.
    Parameters
    ----------
    df: DataFrame
        original dataframe.

    Returns
    -------
    :obj:`list` of :obj:`str`
        sector_names:  a list of the sector names. Note this allows duplicates to make it easier to find the
        corresponding sector.
    :obj:`list` of :obj:`int`
        sector_title_locations: the row number where each of the above sector names occurs in the dataframe
    """
    sector_title_locations = df.loc[df['station'] == '             SECTOR:'].index.values.tolist()
    # sector_title_locations = [mark - 1 for mark in sector_markers]
    sector_names = []
    for state_title_location in sector_title_locations:
        sector_names.append(df.iloc[state_title_location]['sector'])
    return sector_names, sector_title_locations


def get_type_locations(df):
    """
    given the original dataframe, this function gets a list of the fuel types and the rows they appear on.
    Note this allows duplicates.
    Parameters
    ----------
    df: DataFrame
        original dataframe.

    Returns
    -------
    :obj:`list` of :obj:`str`
        type_names: a list of the fuel type names. Note this allows duplicates to make it easier to find the
        corresponding fuel type.
    :obj:`list` of :obj:`int`
        type_title_locations: the row number where each of the above fuel types occurs in the dataframe
    """
    type_title_locations = df.loc[df['station'] == '             TYPE:'].index.values.tolist()
    # type_title_locations = [mark - 1 for mark in type_markers]
    type_names = []
    for type_title_location in type_title_locations:
        type_names.append(df.iloc[type_title_location]['fuel_type'])
    return type_names, type_title_locations


def is_powerplant(row, index, df, num_rows, list_of_not_powerplant_words):
    """
    checks if a row is a powerplant, or if it is something else (e.g. a state, a cell saying "state name," etc.
    Parameters
    ----------
    row: Series
        the full row from the dataframe.
    index: int
        the index of which row we are looking at
    df: DataFrame
        the main dataframe
    num_rows: int
        the total number of rows in the dataframe
    list_of_not_powerplant_words: :obj:`list` of :obj:`str`
        a list of the words that would indicate a row is not a powerplant, e.g. "State Total"

    Returns
    -------
    bool
        True if it's a powerplant, false if it's not a powerplant. Note that units are considered powerplants for this.
    """
    if row["station"] in list_of_not_powerplant_words:
        return False
    if pd.isnull(row['station']):
        return False
    if index < (num_rows-1):
        next_row = df.loc[index+1, :]  # loc is slice by numerical index, iloc is slice by index
        if next_row["station"] == "STATE TOTAL" or next_row["station"] == "REGION TOTAL":
            return False
    return True


def xl_to_csv(xl_path):
    """
    not being used right now, but this converts an excel file to a csv based on the path to the xl file.
    Parameters
    ----------
    xl_path: str
        path to excel file

    Returns
    -------
    nothing as it just pushes it to a csv.
    """
    data_xls = pd.read_excel(xl_path, 'Sheet1', index_col=None)
    csv_path = xl_path.replace(".xls", ".csv")
    data_xls.to_csv(csv_path, encoding='utf-8')
    return


def add_powerplant_to_unit(index, row, df):
    """
    For any units in the dataframe, this adds the powerplant name in front of the unit for the final file.
    Parameters
    ----------
    index: int
        the index of the row we are looking at.
    row: Series
        the current row
    df: DataFrame
        the original dataframe

    Returns
    -------
    Series:
        the modified row,
    DataFrame:
        the modified dataframe
    Str:
        the powerplant associated with the unit.
    """
    previous_row = df.loc[index-1, :]
    if "Unit" not in previous_row["station"]:
        row["station"] = previous_row["station"] + " Unit " + str(int(row['unit']))
        associated_power_plant = previous_row["station"]
        df.loc[index] = row
    else:
        associated_power_plant = previous_row["station"][:-7]
        last_chars = previous_row["station"][-2:]
        replacement = " " + str(int(row['unit'])) if int(row['unit']) <= 10 else str(int(row['unit']))
        row["station"] = previous_row["station"].replace(last_chars, replacement)
        df.loc[index] = row
    return row, df, associated_power_plant


def get_powerplant_row_and_name(current_index, row, df):
    """
    this is what is called to actually get the powerplant name and add it to the unit to get a complete name for the
    row.
    Parameters
    ----------
    current_index: int
        index of the current row
    row: Series
        the current row
    df: DataFrame
        the dataframe
    Returns
    -------
    str:
        the name of the powerplant (which includes the unit number)
    Series:
        the current row which is updated with the combined powerplant and unit name.
    """
    current_row = row
    # get the name of the powerplant from the first column
    powerplant_name = row["station"]  # first column

    # powerplants with just 1 unit have just the powerplant name
    # powerplants with multiple units have the powerplant name, followed by unit 1, unit 2, etc.
    # to deal with this, we check if the first column is "unit"
    if powerplant_name == "Unit":
        # If it is a unit, we want to add the powerplant name to the unit and number it.
        current_row, df, powerplant_name = add_powerplant_to_unit(current_index, row, df)
    return powerplant_name, current_row


def generate_formatted_dataframe(df, date):
    """
    This is the function that actually creates the updated dataframe in the format requested. It gets the locations of
    the regions, states, sectors, and types, and the names of them. it then loops through the dataframe. If a row is a
    powerplant, it updates the name, finds which region, state, sector, and type it should be. then it adds those to a
    list of powerplant rows, and creates a new dataframe from this.
    Parameters
    ----------
    df: DataFrame
        the original dataframe
    date: str
        the date that the export is from
    Returns
    -------
    DataFrame:
        a transformed dataframe in the format requested in the ticket.
    """
    # get the date and number of rows of the data frame

    num_rows = df.shape[0]

    # get lists of names and locations of the names for regions, states, sectors, and types
    region_names, region_title_locations = get_region_locations(df)
    state_names, state_title_locations = get_state_locations(df)
    sector_names, sector_title_locations = get_sector_locations(df)
    type_names, type_title_locations = get_type_locations(df)

    # create empty list so that we can add each row to the list.
    list_of_converted_rows = []

    # define the non powerplant words
    list_of_not_powerplant_words = ["REGION TOTAL", "STATE TOTAL", '             TYPE:', '             SECTOR:']

    # loop through data frame
    for i, j in df.iterrows():
        # checks if the row is a powerplant or if it's a divider row containing state, sector, etc.
        if is_powerplant(j, i, df, num_rows, list_of_not_powerplant_words):

            # get the name of the powerplant and update row with new name
            powerplant_name, current_row = get_powerplant_row_and_name(i, j, df)

            # create the return series
            return_series = {
                "full_name": current_row["station"],
                "date": date,
                "region": region_names[get_desired_index(region_title_locations, i)],
                "state": state_names[get_desired_index(state_title_locations, i)],
                "sector": sector_names[get_desired_index(sector_title_locations, i)],
                "fuel_type": type_names[get_desired_index(type_title_locations, i)],
                "powerstation": powerplant_name,
                "unit": current_row['unit'],
                "monitored_capacity": current_row['monitored_capacity'],
                "todays_program_generation": current_row["todays_program"],
                "todays_actual_generation": current_row["todays_actual_program"],
                "coal_stock": current_row["coal_stock"],
                "capacity_under_outage": current_row['cap_outage'],
                "outage_date": current_row['outage_date'],
                "expected_date": current_row['expected_date'],
                "remarks": current_row['remarks'],
            }
            list_of_converted_rows.append(pd.Series(return_series))

    # return a data frame from this list of converted rows
    return pd.DataFrame(list_of_converted_rows)


def create_filename_for_csv(filepath, date):
    """
    This creates the filename for the new CSV with the updated data structure
    Parameters
    ----------
    filepath: str
        the path to the file
    date: str
        the date that the data was collected from the powerplants

    Returns
    -------
    str:
        the full path to the csv file including the name of the csv file.
    """
    current_date = str(datetime.datetime.now())[0:10]
    path = filepath
    if ".csv" in filepath:
        path = '/'.join(filepath.split('/')[0:-1])
    correct_path = path + "/" if path[-1] != "/" else path
    csv_name = f"india_powerplant_data_from_{date.replace('/','-')}_created_on_{current_date}.csv"
    return correct_path + csv_name


def get_dataframes_from_file_path(file_path):
    """
    Given the file path, this function creates the dataframe and gets the date for the specific CSV.
    Parameters
    ----------
    file_path: str
        the path to the csv file with the data from india
    Returns
    -------
    DataFrame:
        the dataframe
    str:
        the date for the CSV data (i.e when it was taken)
    """
    columns = ["station", "unit", "fuel_type", "sector", "LSP", "monitored_capacity", "todays_program",
               "todays_actual_program", "til_date_program", "till_date_actual", "coal_stock", "cap_outage",
               "outage_date", "expected_date", "remarks", "date"]

    # create initial data frame and define length
    date_df = pd.read_csv(file_path, nrows=2, names=columns)
    df = pd.read_csv(file_path, skiprows=5, names=columns)

    # get date
    date = get_date(date_df)
    return df, date


def get_file_path():
    """
    This uses argparse to get the file path. The user must specify a file path if this is run through the command line.
    Returns
    -------
    str:
        the file path.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="This script will convert a csv file downloaded India's gov report and convert it to the right "
                    "format.")
    parser.add_argument('-p', '--file-path',
                        help="what is the path to the downloaded csv file?")
    args = parser.parse_args()
    file_path = args.file_path if args.file_path \
        else input('What is the path to the downloaded CSV? ')

    return file_path


def main():
    """
    The main function to run if running through the command line. gets file path to csv, creates the dataframe from the
    csv and gets the date, and reformats the data to get a new dataframe with the requested fields.
    Returns
    -------
    nothing, but it does print a success message and where the output CSV file is.
    """

    # get file path
    file_path = get_file_path()

    # print that it is starting
    print("generating output csv...")

    # get the data frames from the file path
    df, date = get_dataframes_from_file_path(file_path)
    # note: if you use the other script to get the CSV, you will need to change how you get the dataframe and the
    # date dataframe which are in this function.

    # generate the returned data frame
    returned_df = generate_formatted_dataframe(df, date)
    # this is the code you will want to use in another script, you just need to generate the dataframe and date

    # create the full csv file name including the path
    path_to_output_csv_file = create_filename_for_csv(file_path, date)

    # create the csv from the data frame
    returned_df.to_csv(path_to_output_csv_file)
    print(f"Success! Your CSV was created: {path_to_output_csv_file}")


if __name__ == "__main__":
    main()
