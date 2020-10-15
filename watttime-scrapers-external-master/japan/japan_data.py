
import datetime
import pytz
import requests
import logging

logger = logging.getLogger('watttime_scrap_japan')
FORMAT = "[%(asctime)s - %(filename)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)


def check_format(data):
	"""
	This function checks the format of the data in the link.
	It is expected that the tables (1hr and 5min) are available in the exact same position, and with the exact same
	number of columns.
	First, the code checks the position of the tables.
	Second, it checks if the number of columns in the table are as expected.
	The 1hr table has 6 cols and the 5 min table has 4 cols.
	If there are any discrepency, an error is logged.
	:param data: Content of the file/link
	:return: An error flag and the position of tables in the file.
	"""
	error_found = False
	table_pos = [i for i in range(len(data)) if 'DATE,TIME,' in data[i]]
	if table_pos[0] != 13:
		logger.error('Position of Actual Demand Performance table may have changed')
		error_found = True
	if table_pos[1] != 54:
		logger.error('Position of Solar Performance table may have changed')
		error_found = True

	# check if all perf table has 6 elements
	if len(data[table_pos[0] + 1].split(',')) != 6:
		logger.error('Number of columns in Actual Demand Performance table is not 6. It is ' +
					 str(len(data[table_pos[0]+ 1].split(','))))
		error_found = True
	if len(data[table_pos[1] + 1].split(',')) != 4:
		logger.error('Number of columns in Actual Demand Performance table is not 4. It is ' +
					 str(len(data[table_pos[1] + 1].split(','))))
		error_found = True

	if not error_found:
		logger.info('Data check complete.')

	return error_found, table_pos


def get_perf_data(data, pos, n_expected):
	"""
	This function reads the tables and gets the latest data.
	Here, the latest data obtained by looping thru all the rows of the table until the performance data is empty (5
	min table) or the usage rate is empty (1hr table).
	The result is an array of associated values.
	If the first row of the table is empty (perhaps at the start of the day), it will return an empty array.
	:param data: Content of the file
	:param pos: Position of the table in the file
	:param n_expected: Total number of rows expected in the table
	:return: Empty list or a list of latest values.
	"""
	perf = []
	for i in range(n_expected):
		rec = data[pos+1+i].strip().split(',')
		date = rec[0].strip()
		time = rec[1].strip()
		if len(rec) > 4:
			pd = rec[2].strip()
			forecast = rec[3].strip()
			usage_rate = rec[4].strip()
			supply = rec[5].strip()

			if '0' in pd and not usage_rate:
				break
			perf.append([date, time, pd, forecast, usage_rate, supply])
		else:
			pd = rec[2].strip()
			solar = rec[3].strip()

			if not pd:
				break
			perf.append([date, time, pd, solar])

	logger.info('Latest data in table at location: ' + str(len(perf)))
	if len(perf) == 0:
		logger.error('No data available in table')
		return []
	return perf[-1]


def format_datapoint(rec):
	"""
	This function formats the values from each table into the datapoint specification given.
	Here, the timezone is localized to Japan and meta data provides the details of each value.
	:param rec: A record of values obtained from the table
	:return: A list of formated values.
	"""
	datapoints = []
	dtime = datetime.datetime.strptime(rec[0] + ' ' + rec[1], '%Y/%m/%d %H:%M')
	timezone = pytz.timezone('Asia/Tokyo')
	dtime_zone_aware = timezone.localize(dtime)

	if len(rec) > 4:
		# Hourly overall Performance Data
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[2])*10, 'ba': 'Tepco Japan',
						   'meta': 'Hourly Performance of the day (in Mega Watt)'})
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[3]) * 10, 'ba': 'Tepco Japan',
						   'meta': 'Hourly Forecast (in Mega Watt)'})
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[4]), 'ba': 'Tepco Japan',
						   'meta': 'Hourly Usage Rate (in %)'})
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[5]) * 10, 'ba': 'Tepco Japan',
						   'meta': 'Hourly Supply Power (in Mega Watt)'})

	else:
		# 5 Min Performance Data with Solar
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[2]) * 10, 'ba': 'Tepco Japan',
						   'meta': '5 min Performance of the day (in Mega Watt)'})
		datapoints.append({'ts': dtime_zone_aware, 'value': int(rec[3]) * 10, 'ba': 'Tepco Japan',
						   'meta': '5 min Solar Power (in Mega Watt)'})

	return datapoints


def read_tepco_japan():
	"""
	This is the main function for scrapping data from Tepco Japan.
	First, the csv file is read from the link.
	Second, the format of the file is checked for errors and the table position is obtained.
	Third, latest data from each table is obtained.
	Forth, the values obtained are formatted.
	Fifth, formatted values are returned.
	:return: A list of formatted datapoints
	"""

	link = "http://www.tepco.co.jp/forecast/html/images/juyo-d-j.csv"
	r = requests.get(link)
	data = r.text.split('\n')

	# Check errors in data format
	error, data_pos = check_format(data)
	if error:
		logger.error('Error found in link. Please check link format.')
		return

	# Get latest data
	overall_hr_perf = get_perf_data(data, data_pos[0], 24)
	solar_5min_perf = get_perf_data(data, data_pos[1], 288)

	# Format data
	datapoints = []
	if len(overall_hr_perf) > 0:
		datapoints.extend(format_datapoint(overall_hr_perf))
	if len(solar_5min_perf) > 0:
		datapoints.extend(format_datapoint(solar_5min_perf))
	logger.info('Data collection complete. Returning values.')

	return datapoints


if __name__ == '__main__':
	datapoints = read_tepco_japan()
