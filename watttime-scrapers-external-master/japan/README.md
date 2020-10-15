# watttime-scrapers-external

watttime_scrap_japan.py: The code collects the latest data from the site (CSV), and depends on the table format and position in the csv file. If there is any change in format, the code will log an error and will not provide any output. The output is in the form of a datapoint dictionary as prescribed.
One key insight is that this energy provider lists their original data in 10000 KW rather than MegaWatt. So, the code converts this data into MegaWatt.
