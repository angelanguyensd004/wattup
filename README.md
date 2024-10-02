# Watt's Up 

Watt's Up is a Plotly Dash application with helpful load visualiziations and includes a  year (2024) load forecasting model for San Diego. 
The model along with the plots are simple, yet provide the needed information to forecast future loads by utilizing historical load and temperature data.
On top of load forecasts, this Dash application also asks the question if median househould income is correlated to average kWh usage. The application 
can only be deployed on my server. However, I have included pictures of the Dash application and the plots created (seen with files with.png). 

# Requirements.txt (Langauge + Libraries used) 
* Python
* Pandas
* Plotly
* Dash
* Scikit-Learn

# Data used
Historical data was largely collected from CAISO (California Independent System Operator). Data was also collected from OpenDataSoft and the 
NOAA for weather data (Selected San Diego Lindbergh Field Weather). Below are the direct links to the data sources: 
* [SANDAG Data](https://www.sangis.org/)
* [Simple Maps Income Data](https://simplemaps.com/city/san-diego/zips/income-household-median)
* [SDGE ZipCode Data from OpenDataSoft](https://data.opendatasoft.com/explore/dataset/sdg-and-e-energy-data%40ornl/table/)
* [CAISO](https://www.caiso.com/generation-transmission/resource-adequacy)
* [San Diego Lindbergh Field Weather](https://www.weather.gov/sgx/cliplot)


# Pages 
* Energy Use & Income in San Diego by ZIPs
* SDGE Load Forecasting
* Data sources

# Results 
How well did the linear regression model perform? Does average kWh change with median household income in San Diego County? 
* Mean absolute error (MAE): 17.59 MWh
* R² value = 0.127793 
