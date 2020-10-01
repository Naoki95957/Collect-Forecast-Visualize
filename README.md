# Collect-Forecast-Visualize
Collect, Forecast, &amp; Visualize – Global Electricity Generation Data

A collaboration between multiple nonprofits, governments, and tech companies is currently building [an AI](https://www.vox.com/energy-and-environment/2019/5/7/18530811/global-power-plants-real-time-pollution-data) to continuously monitor pollution from every power plant in the world from space, using satellite data.

A crucial component of that system is its ability to be trained on a sufficiently large and accurate training dataset. This will be a mix of readily available satellite imagery, combined with accurate ground truth generation data. The purpose of this project is to help build that ground truthing system. Students will implement real-time scrapers for web-based data from power grids around the world and analyze the data for accuracy. 

A forecasting model will be implemented to predict future generation values and a front-end tool will be created to visualize the collected data. 

### Additional info:
Students will be working within a framework provided by WattTime which already includes a robust ETL pipeline, database, and significant support on where to find data and how to interpret it. 

## Members:

### Mentor - [Connor Guest](mailto:connor@watttime.org)

### Proffessor - [Sara Farag](https://www.bellevuecollege.edu/cs/staff/sarag-farag/)

### Team (github links):
  - [Andre Weertman](https://github.com/aweertman)
  - Maximiliano Ayala
  - [Naoki Lucas](https://github.com/Naoki95957)
  - [Vitaliy Stepanov](https://github.com/vitaliybeinspired)

## Project Outcome:
  1. Python code that will sit within an existing WattTime tool which will automatcially scrape, test, and correct data
  2. Forecasting model
  3. Front-end visualization tool of the data

## Technologies:
### This project has four components:
  1. Write scrapers, likely in Python, to scrape data from power grid websites around the world. 
  2. Analyze the scraped data for accuracy. (For example, many coal-fired power plants report emissions that are exactly 1,000 times smaller than is possible, which is a clear sign that they are reporting in the wrong units.) 
  3. Create a forecasting model to predict future generation values 
  4. Build a tool to visualize the data

## Prerequisites:
### Python:

  We will be using [python 3](https://www.python.org/downloads/)
  
  Libraries:
  - Any neccessary libraries TBD
  
### Unit analysis:
 Any neccessary tools TBD
## APIs:
 - [Watttime.org](https://www.watttime.org/api-documentation/#introduction)
    - HTTP requests/responses
    - Details like auth/account TBD
    - [Example code](https://github.com/WattTime/apiv2-example/blob/master/query_apiv2.py)
    
## Misc.:
Current version of readme is mostly comprised of reformatted information found on our outline. 
