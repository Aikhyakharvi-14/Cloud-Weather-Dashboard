import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Read API key securely
API_KEY = st.secrets.get(
    "OPENWEATHER_API_KEY",
    os.getenv("OPENWEATHER_API_KEY", "")
)

BASE_URL = "https://api.openweathermap.org/data/2.5"


# Function to fetch current weather
@st.cache_data(ttl=600)
def get_current_weather(city):

    url = f"{BASE_URL}/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=15)

    response.raise_for_status()

    return response.json()


# Function to fetch five-day forecast
@st.cache_data(ttl=600)
def get_forecast(city):

    url = f"{BASE_URL}/forecast"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=15)

    response.raise_for_status()

    return response.json()
def process_forecast(forecast_data):

    records = []

    for item in forecast_data["list"]:

        records.append({
            "Date": item["dt_txt"],
            "Temperature": item["main"]["temp"],
            "Feels Like": item["main"]["feels_like"],
            "Humidity": item["main"]["humidity"],
            "Wind Speed": item["wind"]["speed"],
            "Rainfall": item.get("rain", {}).get("3h", 0),
            "Weather": item["weather"][0]["description"]
        })

    df = pd.DataFrame(records)

    df["Date"] = pd.to_datetime(df["Date"])

    return df

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="Cloud Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# -----------------------------------
# API CONFIGURATION
# -----------------------------------

API_KEY = st.secrets.get(
    "OPENWEATHER_API_KEY",
    os.getenv("OPENWEATHER_API_KEY", "")
)

BASE_URL = "https://api.openweathermap.org/data/2.5"


# -----------------------------------
# FETCH CURRENT WEATHER
# -----------------------------------

@st.cache_data(ttl=600)
def get_current_weather(city):

    response = requests.get(
        f"{BASE_URL}/weather",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
        timeout=15
    )

    response.raise_for_status()

    return response.json()


# -----------------------------------
# FETCH WEATHER FORECAST
# -----------------------------------

@st.cache_data(ttl=600)
def get_forecast(city):

    response = requests.get(
        f"{BASE_URL}/forecast",
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        },
        timeout=15
    )

    response.raise_for_status()

    return response.json()


# -----------------------------------
# PROCESS FORECAST DATA
# -----------------------------------

def process_forecast(data):

    records = []

    for item in data["list"]:

        records.append({
            "Date": item["dt_txt"],
            "Temperature": item["main"]["temp"],
            "Humidity": item["main"]["humidity"],
            "Wind Speed": item["wind"]["speed"],
            "Rainfall": item.get("rain", {}).get("3h", 0),
            "Weather": item["weather"][0]["description"]
        })

    df = pd.DataFrame(records)

    df["Date"] = pd.to_datetime(df["Date"])

    return df


# -----------------------------------
# DASHBOARD DESIGN
# -----------------------------------

st.title("🌤️ Cloud-Based Weather Dashboard")

st.write(
    "Monitor real-time weather conditions "
    "and explore upcoming weather forecasts."
)

st.divider()

# -----------------------------------
# CITY SEARCH
# -----------------------------------

st.sidebar.header("Weather Search")

city = st.sidebar.text_input(
    "Enter City Name",
    value="Bangalore"
)

search = st.sidebar.button(
    "Get Weather",
    use_container_width=True
)

st.sidebar.caption(
    "Powered by OpenWeather API"
)

if "searched_city" not in st.session_state:
    st.session_state.searched_city = "Bangalore"

if search:
    if city.strip():
        st.session_state.searched_city = city.strip()
    else:
        st.sidebar.warning("Please enter a city name.")

selected_city = st.session_state.searched_city

# -----------------------------------
# API KEY VALIDATION
# -----------------------------------

if not API_KEY:

    st.error(
        "API key not found. Configure "
        "OPENWEATHER_API_KEY in secrets.toml."
    )

    st.stop()

# -----------------------------------
# FETCH DATA
# -----------------------------------

try:

    with st.spinner("Fetching weather information..."):

        current = get_current_weather(selected_city)

        forecast = get_forecast(selected_city)

    forecast_df = process_forecast(forecast)

    st.subheader(f"Weather in {current['name']}")

    st.caption(
        f"{current['sys']['country']} | "
        f"Last updated: "
        f"{pd.to_datetime(current['dt'], unit='s', utc=True)}"
    )

    # -----------------------------------
    # CURRENT WEATHER
    # -----------------------------------

    temperature = current["main"]["temp"]

    description = current["weather"][0]["description"]

    icon = current["weather"][0]["icon"]

    st.markdown(
        f"## {temperature:.1f} °C"
    )

    st.write(f"**{description.title()}**")

    st.image(
        f"https://openweathermap.org/img/wn/{icon}@2x.png",
        width=90
    )

    st.divider()

    # -----------------------------------
    # WEATHER METRICS
    # -----------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Feels Like",
        f"{current['main']['feels_like']:.1f} °C"
    )

    col2.metric(
        "Humidity",
        f"{current['main']['humidity']}%"
    )

    col3.metric(
        "Wind Speed",
        f"{current['wind']['speed']} m/s"
    )

    col4.metric(
        "Pressure",
        f"{current['main']['pressure']} hPa"
    )

    st.divider()

    # -----------------------------------
    # TEMPERATURE CHART
    # -----------------------------------

    st.subheader("🌡️ Temperature Forecast")

    fig_temp = px.line(
        forecast_df,
        x="Date",
        y="Temperature",
        markers=True,
        title="Temperature for the Next Five Days"
    )

    fig_temp.update_layout(
        xaxis_title="Date and Time",
        yaxis_title="Temperature (°C)",
        template="plotly_dark"
    )

    st.plotly_chart(
        fig_temp,
        use_container_width=True
    )

    # -----------------------------------
    # HUMIDITY AND WIND CHARTS
    # -----------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("💧 Humidity Analysis")

        fig_humidity = px.area(
            forecast_df,
            x="Date",
            y="Humidity",
            title="Humidity Trend"
        )

        fig_humidity.update_layout(
            template="plotly_dark",
            yaxis_title="Humidity (%)"
        )

        st.plotly_chart(
            fig_humidity,
            use_container_width=True
        )

    with col2:

        st.subheader("💨 Wind Speed Analysis")

        fig_wind = px.bar(
            forecast_df,
            x="Date",
            y="Wind Speed",
            title="Wind Speed Forecast"
        )

        fig_wind.update_layout(
            template="plotly_dark",
            yaxis_title="Wind Speed (m/s)"
        )

        st.plotly_chart(
            fig_wind,
            use_container_width=True
        )

    # -----------------------------------
    # DAILY FORECAST SUMMARY
    # -----------------------------------

    st.subheader("📅 Five-Day Weather Forecast")

    daily = (
        forecast_df
        .groupby(forecast_df["Date"].dt.date)
        .agg(
            Min_Temp=("Temperature", "min"),
            Max_Temp=("Temperature", "max"),
            Avg_Humidity=("Humidity", "mean"),
            Rainfall=("Rainfall", "sum"),
            Weather=("Weather", "first")
        )
        .reset_index()
    )

    daily.columns = [
        "Date",
        "Minimum Temperature",
        "Maximum Temperature",
        "Average Humidity",
        "Forecast Rainfall",
        "Weather"
    ]

    st.dataframe(
        daily.round(1),
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------
    # DOWNLOAD FORECAST DATA
    # -----------------------------------

    csv = forecast_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Weather Data",
        data=csv,
        file_name="weather_forecast.csv",
        mime="text/csv"
    )

    st.success("Weather dashboard updated successfully!")

except requests.exceptions.HTTPError as e:

    if e.response is not None and e.response.status_code == 404:
        st.error("City not found. Please check the city name.")

    elif e.response is not None and e.response.status_code == 401:
        st.error("Invalid API key or API access not yet activated.")

    elif e.response is not None and e.response.status_code == 429:
        st.error("API request limit reached. Please try again later.")

    else:
        st.error(f"Weather API error: {e}")

except requests.exceptions.RequestException as e:

    st.error(f"Network connection error: {e}")

except (KeyError, ValueError, TypeError) as e:

    st.error(f"Unable to process weather data: {e}")
