import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import threading
import webbrowser

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

#load data paths for 5 years of load data, weather data, and true 2024 (JAN-JUNE)
filepaths_load = [
    r"data\historicalemshourlyload-2019.csv",
    r"data\historicalemshourlyload-2020.csv",
    r"data\historicalemshourlyload-2021.csv",
    r"data\historicalemshourlyload-2022.csv",
    r"data\historicalemshourlyloadfor2023.csv"
]

filepaths_weather = [
    r"data\AverageWeatherSD2019.csv",
    r"data\AverageWeatherSD2020.csv",
    r"data\AverageWeatherSD2021.csv",
    r"data\AverageWeatherSD2022.csv",
    r"data\AverageWeatherSD2023.csv"
]

filepaths_true = [
    r"data\historicalemshourlyloadforjanuary2024 (1).csv",
    r"data\historicalemshourlyloadforfebruary2024 (1).csv",
    r"data\historicalemshourlyloadformarch2024 (1).csv",
    r"data\historical-ems-hourly-load-for-april-2024 (2).csv",
    r"data\historical-ems-hourly-load-for-may-2024.csv",
    r"data\historical-ems-hourly-load-for-june-2024.csv",
]

#load and process each year's load data
load_data = []
for filepath in filepaths_load:
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        print(f"Loaded {filepath} with shape: {df.shape}")

        df["Date"] = pd.to_datetime(df["Date"])  #ensure correct column
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month

        if "SDGE" in df.columns:
            monthly_avg = df.groupby(["Year", "Month"])["SDGE"].mean().reset_index()
            monthly_avg.columns = ["Year", "Month", "Energy_Consumption"]
            load_data.append(monthly_avg)
        else:
            print(f"'SDGE' column not found in {filepath}.")
    except Exception as e:
        print(f"Error loading {filepath}: {e}")

#error with loading date column for may, june 2024, check if column contains byte strings to fix 
if df["Date"].dtype == "object":  #check if the column is of type object
    df["Date"] = df["Date"].apply(lambda x: x.decode("utf-8") if isinstance(x, bytes) else x)

#convert column date to datetime format just in case if string og 
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
# Combine all monthly average load data
if load_data:
    all_load_data = pd.concat(load_data, ignore_index=True)
else:
    print("No load data was loaded.")

#load and process each year's weather data
weather_data = []
for filepath in filepaths_weather:
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        year = int(filepath.split("SD")[-1][0:4])
        
        for index, row in df.iterrows():
            weather_data.append({"Year": year, "Month": row['MONTH'], "Temperature": row["AVTEMP"]})
    except Exception as e:
        print(f"Error loading {filepath}: {e}")


#convert weather data list to DataFrame
if weather_data:
    all_weather_data = pd.DataFrame(weather_data)
else:
    print("No weather data was loaded.")

#merge the two DataFrames year and month
if load_data and weather_data:
    merged_data = pd.merge(all_load_data, all_weather_data, on=["Year", "Month"])
else:
    print("One or both data sets are empty; cannot create plot.")

#load the trueload sdge data
true_data = []
for filepath in filepaths_true:
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        print(f"Loaded {filepath} with shape: {df.shape}")
        print("Columns found:", df.columns.tolist())  

        #clean column names
        df.columns = df.columns.str.strip()

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            if df["Date"].isnull().all():
                print(f"All dates are invalid in {filepath}. Skipping this file.")
                continue  #skip to the next file

            df["Year"] = df["Date"].dt.year
            df["Month"] = df["Date"].dt.month

            if "SDGE" in df.columns:
                monthly_avg = df.groupby(["Year", "Month"])["SDGE"].mean().reset_index()
                monthly_avg.columns = ["Year", "Month", "Energy_Consumption"]
                true_data.append(monthly_avg)  
            else:
                print(f"'SDGE' column not found in {filepath}.")
        else:
            print(f"'Date' column not found in {filepath}. Skipping this file.")
    except Exception as e:
        print(f"Error loading {filepath}: {e}")

#combine all monthly average true load data
if true_data:
    all_true_load_data = pd.concat(true_data, ignore_index=True)
else:
    print("No true load data was loaded.")

#form dual-axis continuous line plot
fig = go.Figure()

#add predicted energy consumption as a line trace
fig.add_trace(go.Scatter(
    x=merged_data["Year"].astype(str) + '-' + merged_data["Month"].astype(str),
    y=merged_data["Energy_Consumption"],
    mode="lines+markers",
    name="Energy Consumption (MWh)",
    line=dict(color="forestgreen"),
    yaxis="y1"
))

# temperature as a line trace
fig.add_trace(go.Scatter(
    x=merged_data["Year"].astype(str) + '-' + merged_data["Month"].astype(str),
    y=merged_data["Temperature"],
    mode="lines+markers",
    name="Average Temperature (°F)",
    line=dict(color="coral"),
    yaxis="y2"
))

#update layout 
fig.update_layout(
    title="Energy Consumption plotted with Temperature (2019-2023)",
    xaxis=dict(title="Year", tickmode="array"),
    yaxis=dict(title="Average Energy Consumption (MWh)", side="left", titlefont=dict(color="green")),
    yaxis2=dict(title="Average Temperature (°F)", side="right", overlaying="y", titlefont=dict(color="red"))
)

#convert to HTML
layout_html = pio.to_html(fig, full_html=False)


#fancy feature engineering! 
merged_data["Year_Month"] = merged_data["Year"].astype(str) + '-' + merged_data['Month'].astype(str)
merged_data["Month_Sin"] = (merged_data["Month"] % 12) / 12 * (2 * 3.14159)
merged_data["Month_Cos"] = (merged_data["Month"] % 12) / 12 * (2 * 3.14159)

#linear regression model
X = merged_data[["Temperature", "Month_Sin", "Month_Cos"]]
y = merged_data["Energy_Consumption"]

#divide the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#fit the model
model = LinearRegression()
model.fit(X_train, y_train)

#make predictions on the test set
y_pred = model.predict(X_test)

#test the model
rmse = mean_squared_error(y_test, y_pred, squared=False)
print(f'RMSE: {rmse}')

#forecast for 2024
#added an adjustment for temperatures to reflect seasonal patterns
weather_2024 = pd.DataFrame({
    "Year": 2024,
    "Month": range(1, 13),
    "Temperature": [57, 59, 60, 62, 65, 75, 78, 80, 70, 68, 61, 55]  # predicted temperatures from historical data (2019-2023)
})

weather_2024["Month_Sin"] = (weather_2024["Month"] % 12) / 12 * (2 * 3.14159)
weather_2024["Month_Cos"] = (weather_2024["Month"] % 12) / 12 * (2 * 3.14159)

#predict energy consumption for 2024
X_2024 = weather_2024[['Temperature', 'Month_Sin', 'Month_Cos']]
forecasted_load = model.predict(X_2024)

#seasonal adjustments
forecasted_load[0] *= 1.10  # January
forecasted_load[1] *= 1.05  # February 
forecasted_load[2] *= 0.95  # March
forecasted_load[3] *= 0.90  # April
forecasted_load[4] *= 0.85  # May
forecasted_load[5] *= 0.80  # June
forecasted_load[6] *= 0.90  # July
forecasted_load[8] *= 1.05  # September
forecasted_load[10] *= 1.05 # November
forecasted_load[11] *= 1.18 # December

#combine predictions with weather data for plotting
weather_2024['Predicted_Energy_Consumption'] = forecasted_load

#calculate Mean Absolute Error (MAE) for the first 6 months of 2024
if not all_true_load_data.empty and len(all_true_load_data) == 6:
    mae = (abs(weather_2024["Predicted_Energy_Consumption"][:6] - all_true_load_data['Energy_Consumption'])).mean()
    print(f'Mean Absolute Error: {mae:.2f} MWh')
else:
    mae = None

#create graph
fig_forecast = go.Figure()

#add forecasted energy consumption
fig_forecast.add_trace(go.Scatter(
    x=weather_2024["Month"].astype(str),
    y=weather_2024["Predicted_Energy_Consumption"],
    mode="lines+markers",
    name="Predicted Energy Consumption (2024)",
    line=dict(color="green")
))

#add true energy consumption to the forecast 
if not all_true_load_data.empty:
    fig_forecast.add_trace(go.Scatter(
        x=all_true_load_data["Month"].astype(str),
        y=all_true_load_data["Energy_Consumption"],
        mode="lines+markers",
        name="True Energy Consumption (2024)",
        line=dict(color="red")
    ))

#update layout for the forecast
fig_forecast.update_layout(
    title="Forecasted Energy Consumption for 2024",
    xaxis=dict(title="Month"),
    yaxis=dict(title="Energy Consumption (MWh)"),
    legend=dict(x=0, y=1),
    annotations=[
        dict(
            x=0.5,
            y=0.95,
            xref="paper",
            yref="paper",
            text=f'Mean Absolute Error: {mae:.2f} MWh' if mae is not None else 'No MAE calculated',
            showarrow=False,
            font=dict(size=12)
        )
    ]
)

forecast_html = pio.to_html(fig_forecast, full_html=False)

#load SDGEResidentialData.csv
filepath_SD = r"data\SDGEResidentialData.csv"
dm = pd.read_csv(filepath_SD)

filtered_dm = dm[(dm["CustomerClass"] == "R") & (dm["AveragekWh"] > 0)]
filtered_dm["Month"] = filtered_dm["Month"].astype(str)
filtered_dm["ZipCode"] = filtered_dm["ZipCode"].astype(str)
filtered_dm = filtered_dm.drop_duplicates(subset=["ZipCode", "Month"])

heatmap_data = filtered_dm.pivot(index="ZipCode", columns="Month", values="AveragekWh")
heatmap_data = heatmap_data.fillna(0)

z = heatmap_data.values
y = heatmap_data.index
x = heatmap_data.columns

fig_heatmap = go.Figure(data=go.Heatmap(
    z=z,
    x=x,
    y=y,
    colorscale="turbo_r",
    colorbar=dict(title="Average kWh per Household")
))

fig_heatmap.update_layout(
    title="Average kWh per Household by ZIP Code and Month in San Diego County (2024)",
    xaxis_title="Month",
    yaxis_title="ZIP Code",
    xaxis_nticks=len(x)
)

heatmap_html = pio.to_html(fig_heatmap, full_html=False)

#load ZipCodeIncomeData.csv
filepath_income = r"data\ZipCodeIncomeData.csv"
income_zip = pd.read_csv(filepath_income)
income_zip.rename(columns={"zipcode": "ZipCode"}, inplace=True)
income_zip["ZipCode"] = income_zip["ZipCode"].astype(str)

#combine mean energy data with income data
average_energy = filtered_dm.groupby("ZipCode")["AveragekWh"].mean().reset_index()
average_energy.rename(columns={"AveragekWh": "Avg_kWh_per_Household"}, inplace=True)
average_energy["ZipCode"] = average_energy["ZipCode"].astype(str)

merged_data = pd.merge(average_energy, income_zip, on="ZipCode")

# Scatter plot with median income and average kWh
fig_scatter = px.scatter(
    merged_data, 
    x="ZipCode", 
    y="Avg_kWh_per_Household",
    color="income_household_median",
    color_continuous_scale="viridis_r", 
    title="Average kWh per Household by ZIP Code with Median Household Income in San Diego County (2024)",
    labels={"ZipCode": "ZIP Code", "Avg_kWh_per_Household": "Average kWh per Household", "income_household_median": "Median Household Income"}
) 

fig_scatter.update_traces(marker=dict(size=20))

scatter_html = pio.to_html(fig_scatter, full_html=False)

#create scatter plot with trendline
fig_trendline = px.scatter(
    merged_data, 
    x="income_household_median", 
    y="Avg_kWh_per_Household",
    color="income_household_median",
    color_continuous_scale="algae",
    title="Median Household Income in Relationship with Average kWh Usage in San Diego (2024)",
    labels={"Avg_kWh_per_Household": "Average kWh per Household", "income_household_median": "Median Household Income"},
    trendline="ols"
) 

fig_trendline.update_traces(marker=dict(size=15))

trendline_html = pio.to_html(fig_trendline, full_html=False)


dataframes = []

#created loop to load DataFrames 
for filepath in filepaths_load:
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        
        #rename "HE" to 'HR"
        if "HE" in df.columns:
            df.rename(columns={"HE": "HR"}, inplace=True)
        
        #convert "HR" to integer
        df["HR"] = df["HR"].astype(int)
        
        #make "Date" column to datetime format
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        
        # Create 'Weekday' column
        df["Weekday"] = df["Date"].dt.day_name()
        
        # Append the DataFrame to the list
        dataframes.append(df)

        # Print the shape of the DataFrame to verify loading
        print(f"Loaded {filepath} with shape: {df.shape}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

# check to see if dataframes list is empty before concatenating
if dataframes:
    combined_data = pd.concat(dataframes, ignore_index=True)
    print("DataFrames concatenated successfully - let's gooooo.")
else:
    print("No DataFrames to concatenate.")

if "Weekday" in combined_data.columns:
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", 'Saturday', 'Sunday']
    combined_data["Weekday"] = pd.Categorical(combined_data["Weekday"], categories=weekday_order, ordered=True)

    #calc mean energy consumption
    mean_data = combined_data.groupby(["HR", "Weekday"])["SDGE"].mean().unstack(fill_value=0)
    
    z_forecast = mean_data.values
    y_forecast = mean_data.index.astype(str)
    x_forecast = mean_data.columns

    fig_fiveyear = go.Figure(data=go.Heatmap(
        z=z_forecast,
        x=x_forecast,
        y=y_forecast,
        colorscale="viridis_r", 
        colorbar=dict(title="MWh")
    ))

    fig_fiveyear.update_layout(
        title="Average Energy Consumption in MWh by Hour and Weekday (2019-2023)",
        xaxis_title="Weekday",
        yaxis_title="Hour",
        yaxis=dict(tickvals=list(mean_data.index), ticktext=list(mean_data.index)),
    )
else:
    print("Combined data does not contain 'Weekday' column; cannot proceed with plotting.")


fiveyear_html = pio.to_html(fig_fiveyear, full_html=False)


#!!!!start of dash page!!!


#layout for the home page
home_layout = html.Div([
    html.H1("Home Page"),
    html.P("Welcome to the home page! As a personal project, I created this application to provide insights into energy consumption and weather patterns in San Diego. I specifically chose San Diego because it's my hometown and is obviously the best city in California :) ")
    
])

#layout for the energy consumption page
SDenergyconsumption_layout = html.Div([
    html.H1("San Diego Residential Energy Consumption by ZIP Code"),
    html.P("How does average kWh change with median household income in San Diego County?"),
    html.Div([
        html.Div([
            html.Iframe(srcDoc=heatmap_html, style={"width": "100%", "height": "100%", "border": "none"})
        ], style={"flex": "1", "margin-right": "10px", "min-width": "0"}),
        html.Div([
            html.Iframe(srcDoc=scatter_html, style={"width": "100%", "height": "100%", "border": "none"})
        ], style={"flex": "1", "margin-left": "10px", "min-width": "0"})
    ], style={"display": "flex", "justify-content": "space-between", "flex-wrap": "wrap", "height": "calc(50vh - 20px)"}),
    html.Div([
        html.Iframe(srcDoc=trendline_html, style={"width": "100%", "height": "100%", "border": "none"})
    ], style={"width": "100%", "height": "calc(50vh - 20px)", "margin-top": "20p"})
], style={"padding": "20px", "height": "100vh", "overflow": "hidden", "box-sizing": "border-box"})

#layout for the sdge load forecasting page
SDGE_load_forecasting_layout = html.Div([
    html.H1("SDGE Load Forecasting"),
    html.Div([
        html.Div([
            html.Iframe(srcDoc=fiveyear_html, style={"width": "100%", "height": "100%", "border": "none"})
        ], style={"flex": "1", "margin-right": "10px", "min-width": "0"}),
        html.Div([
            html.Iframe(srcDoc=layout_html, style={"width": "100%", "height": "100%", "border": "none"})
        ], style={"flex": "1", "margin-left": "10px", "min-width": "0"})
    ], style={"display": "flex", "justify-content": "space-between", "flex-wrap": "wrap", "height": "calc(50vh - 20px)"}),
    html.Div([
        html.Iframe(srcDoc=forecast_html, style={"width": "100%", "height": "100%", "border": "none"})
    ], style={"width": "100%", "height": "calc(50vh - 20px)", "margin-top": "20p"})
], style={"padding": "20px", "height": "100vh", "overflow": "hidden", "box-sizing": "border-box"})

Data_layout = html.Div([
    html.H1("Data Sources"), 
    html.P("For this project, I acquired data from the following websites and pages:"),
    html.Div([
        html.A("SANDAG Data", href="https://www.sangis.org/", target="_blank", style={'display': 'block'}),
        html.A("Simple Maps Income Data", href="https://simplemaps.com/city/san-diego/zips/income-household-median", target="_blank", style={"display": "block"}),
        html.A("SDGE ZipCode Data from OpenDataSoft", href="https://data.opendatasoft.com/explore/dataset/sdg-and-e-energy-data%40ornl/table/", target="_blank", style={"display": "block"}),
        html.A("CAISO", href="https://www.caiso.com/generation-transmission/resource-adequacy", target="_blank", style={"display": "block"}),
        html.A("San Diego Lindbergh Field Weather", href="https://www.weather.gov/sgx/cliplot", target="_blank", style={"display": "block"}),
    ])
])


#prepare dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Energy Use & Income in San Diego by ZIPs", href="/SDenergyconsumption")),
            dbc.NavItem(dbc.NavLink("SDGE Load Forecasting", href="/SDGEloadforecasting")),
            dbc.NavItem(dbc.NavLink("Data Sources", href= "/Data"))
        ]),
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content", style={"padding": "20px"}),
], fluid=True)

@app.callback(Output("page-content", "children"),
              [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/SDenergyconsumption":
        return SDenergyconsumption_layout
    elif pathname == "/SDGEloadforecasting":
        return SDGE_load_forecasting_layout
    elif pathname == "/Data":
        return Data_layout
    else:
        return home_layout

def open_browser():
    import time
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:8050/")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run_server(debug=True)
