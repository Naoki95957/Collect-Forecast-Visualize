# Collect, Forecast, & Visualize – Global Electricity Generation Data.

![Sat Image](https://cdn.vox-cdn.com/thumbor/xEsmQD9pDOqW9jpyfc_m85MQtx4=/0x0:3000x2000/1820x1213/filters:focal(1495x526:1975x1006)/cdn.vox-cdn.com/uploads/chorus_image/image/63748384/shutterstock_229816288.0.jpg)



A collaboration between multiple nonprofits, governments, and tech companies is currently building [an AI](https://www.vox.com/energy-and-environment/2019/5/7/18530811/global-power-plants-real-time-pollution-data) to continuously monitor pollution from every power plant in the world from space, using satellite data.

A crucial component of that system is its ability to be trained on a sufficiently large and accurate training dataset. This will be a mix of readily available satellite imagery, combined with accurate ground truth generation data. The purpose of this project is to help build that ground truthing system. Students will implement real-time scrapers for web-based data from power grids around the world and analyze the data for accuracy. 

A forecasting model will be implemented to predict future generation values and a front-end tool will be created to visualize the collected data. 

Students will be working within a framework provided by WattTime which already includes a robust ETL pipeline, database, and significant support on where to find data and how to interpret it. 

### Mentor - [Connor Guest](mailto:connor@watttime.org)

[Press Release FAQ (PR)](https://github.com/Naoki95957/Collect-Forecast-Visualize/blob/vitaliybeinspired-patch-1/Documents/Press%20Release%20FAQ.pdf)

[Software Design Document (SDD)](https://github.com/Naoki95957/Collect-Forecast-Visualize/blob/vitaliybeinspired-patch-1/Documents/Software%20Design%20Document.pdf)




### Proffessor - [Dr. Sara Farag](https://www.bellevuecollege.edu/cs/staff/sarag-farag/)

### Software Engineers:
  - [Andre Weertman](https://github.com/aweertman)
  - [Maximiliano Ayala](https://github.com/Ayalaboy)
  - [Naoki Lucas](https://github.com/Naoki95957)
  - [Vitaliy Stepanov](https://github.com/vitaliybeinspired)

## Project Outcome:
  1. Python code that will sit within an existing WattTime tool which will automatcially scrape, test, and correct data
  2. Forecasting model
  3. Front-end visualization tool of the data

### This project has four components:
  1. Write scrapers, likely in Python, to scrape data from power grid websites around the world. 
  2. Analyze the scraped data for accuracy. (For example, many coal-fired power plants report emissions that are exactly 1,000 times smaller than is possible, which is a clear sign that they are reporting in the wrong units.) 
  3. Create a forecasting model to predict future generation values 
  4. Build a tool to visualize the data

### Technologies:
   [Python 3](https://www.python.org/downloads/)  
  - arrow
  - bs4
  - datetime
  - requests
  - selenium
  - pandas
  
  You can install all required python modules with `pip install -r requirments.txt`
  (You'll need to manually install pandas due to different instructions per OS)
  
## APIs:
 - [Watttime.org](https://www.watttime.org/api-documentation/#introduction)
    - HTTP requests/responses
    - Details like auth/account TBD
    - [Example code](https://github.com/WattTime/apiv2-example/blob/master/query_apiv2.py)
    

