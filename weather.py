import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import time

# API settings
API_KEY = "3edb4ae23e76cb211977b49f0ac13c1a"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Uzbekistan cities with API names and coordinates
UZB_CITIES = {
    "Toshkent": ("Tashkent", 41.2995, 69.2401),
    "Samarqand": ("Samarkand", 39.6542, 66.9758),
    "Buxoro": ("Bukhara", 39.7686, 64.4556),
    "Farg'ona": ("Fergana", 40.3842, 71.7843),
    "Andijon": ("Andijan", 40.7833, 72.3500),
    "Namangan": ("Namangan", 40.9983, 71.6726),
    "Xorazm": ("Urgench", 41.5500, 60.6333),
    "Qashqadaryo": ("Qarshi", 38.8600, 65.8000),
    "Surxondaryo": ("Termiz", 37.2242, 67.2783),
    "Navoiy": ("Navoiy", 40.1000, 65.3667),
    "Jizzax": ("Jizzakh", 40.1000, 67.8500),
    "Sirdaryo": ("Gulistan", 40.5000, 68.7833),
    "Nukus": ("Nukus", 42.4667, 59.6000)
}

# Icons for weather conditions
WEATHER_ICONS = {
    "01d": "☀️", "01n": "🌙",  # clear sky
    "02d": "⛅", "02n": "☁️",  # few clouds
    "03d": "☁️", "03n": "☁️",  # scattered clouds
    "04d": "☁️", "04n": "☁️",  # broken clouds
    "09d": "🌧️", "09n": "🌧️",  # shower rain
    "10d": "🌦️", "10n": "🌧️",  # rain
    "11d": "⛈️", "11n": "⛈️",  # thunderstorm
    "13d": "❄️", "13n": "❄️",  # snow
    "50d": "🌫️", "50n": "🌫️",  # mist
}

# Weather condition colors
WEATHER_COLORS = {
    "01d": "#FFB366", "01n": "#4A5568",  # clear sky
    "02d": "#90CDF4", "02n": "#4A5568",  # few clouds
    "03d": "#90CDF4", "03n": "#4A5568",  # scattered clouds
    "04d": "#718096", "04n": "#4A5568",  # broken clouds
    "09d": "#3182CE", "09n": "#2A4365",  # shower rain
    "10d": "#3182CE", "10n": "#2A4365",  # rain
    "11d": "#6B46C1", "11n": "#44337A",  # thunderstorm
    "13d": "#E2E8F0", "13n": "#CBD5E0",  # snow
    "50d": "#A0AEC0", "50n": "#718096",  # mist
}


@st.cache_data(ttl=600)
def show_weather(region):
    if region not in UZB_CITIES:
        return None
    city_name, lat, lon = UZB_CITIES[region]
    params = {"q": city_name + ",UZ", "appid": API_KEY, "units": "metric", "lang": "uz"}
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if response.status_code == 200:
            return {
                "temp": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"]["pressure"],
                "rain_chance": data.get("rain", {}).get("1h", 0),
                "description": data["weather"][0]["description"].capitalize(),
                "icon": data["weather"][0]["icon"],
                "date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                "lat": lat,
                "lon": lon
            }
        else:
            return None
    except requests.exceptions.RequestException:
        return None


@st.cache_data(ttl=1800)
def get_forecast(region):
    if region not in UZB_CITIES:
        return None
    city_name, _, _ = UZB_CITIES[region]
    params = {"q": city_name + ",UZ", "appid": API_KEY, "units": "metric", "cnt": 40, "lang": "uz"}
    try:
        response = requests.get(FORECAST_URL, params=params)
        data = response.json()
        if response.status_code == 200:
            temps, rain_probs, dates, icons, wind_speeds, humidities = [], [], [], [], [], []
            for entry in data["list"]:
                temps.append(round(entry["main"]["temp"]))
                rain_probs.append(entry.get("pop", 0) * 100)
                dates.append(datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S"))
                icons.append(entry["weather"][0]["icon"])
                wind_speeds.append(entry["wind"]["speed"])
                humidities.append(entry["main"]["humidity"])

            # Get daily forecasts (use noon forecasts for each day)
            daily_dates, daily_temps, daily_icons, daily_rain_probs, daily_descriptions, daily_wind_speeds, daily_humidities = [], [], [], [], [], [], []
            current_date = dates[0].date()

            # Group forecast by date
            date_groups = {}
            for i, date in enumerate(dates):
                date_key = date.date()
                if date_key not in date_groups:
                    date_groups[date_key] = []
                date_groups[date_key].append(i)

            # Get 7 days of forecasts with full data
            for i in range(7):  # Get 7 days
                target_date = current_date + timedelta(days=i)
                if target_date in date_groups:
                    indices = date_groups[target_date]
                    # Try to get noon forecast
                    noon_index = None
                    for idx in indices:
                        if 11 <= dates[idx].hour <= 14:
                            noon_index = idx
                            break

                    # If no noon forecast, take the first one of the day
                    if noon_index is None and indices:
                        noon_index = indices[0]

                    if noon_index is not None:
                        daily_dates.append(dates[noon_index])
                        daily_temps.append(temps[noon_index])
                        daily_icons.append(icons[noon_index])
                        daily_rain_probs.append(rain_probs[noon_index])
                        daily_wind_speeds.append(wind_speeds[noon_index])
                        daily_humidities.append(humidities[noon_index])

            # Calculate weekly averages
            weekly_avg_temp = sum(temps[:40]) / len(temps[:40]) if temps else 0
            weekly_avg_rain_prob = sum(rain_probs[:40]) / len(rain_probs[:40]) if rain_probs else 0

            return {
                "dates": dates,
                "temps": temps,
                "rain_probs": rain_probs,
                "icons": icons,
                "wind_speeds": wind_speeds,
                "humidities": humidities,
                "daily_dates": daily_dates,
                "daily_temps": daily_temps,
                "daily_icons": daily_icons,
                "daily_rain_probs": daily_rain_probs,
                "daily_wind_speeds": daily_wind_speeds,
                "daily_humidities": daily_humidities,
                "weekly_avg_temp": round(weekly_avg_temp, 1),
                "weekly_avg_rain_prob": round(weekly_avg_rain_prob, 1)
            }
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def apply_weather_css():
    """Apply the CSS for the weather page"""
    st.markdown("""
    <style>
        /* Modern gradient background with aurora animation */
        @keyframes aurora {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .stApp {
            background: linear-gradient(-45deg, #0093E9, #80D0C7, #5D26C1, #a17fe0);
            background-size: 400% 400%;
            animation: aurora 15s ease infinite;
        }

        /* Modern glass morphism effect */
        .glass-card {
            background: rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(9.8px);
            -webkit-backdrop-filter: blur(9.8px);
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 30px;
            color: white;
            margin-bottom: 20px;
        }

        /* Header styling */
        .header {
            text-align: center;
            padding: 40px 0;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #ffffff, #e0e0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.85;
            max-width: 600px;
            margin: 10px auto;
            color: white;
        }

        /* Weather card with pulse animation */
        .weather-card {
            position: relative;
            overflow: hidden;
            border-radius: 16px;
            padding: 30px;
            color: white;
            background: rgba(0, 0, 0, 0.2);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
            min-height: 260px;
        }

        .pulse {
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            height: 400px;
            width: 400px;
            position: absolute;
            right: -100px;
            top: -100px;
            z-index: 0;
            opacity: 0;
            animation: pulse 5s infinite;
        }

        @keyframes pulse {
            0% {transform: scale(0.8); opacity: 0;}
            50% {transform: scale(1); opacity: 0.3;}
            100% {transform: scale(1.2); opacity: 0;}
        }

        .weather-card h2 {
            font-size: 2rem;
            margin: 0;
            z-index: 1;
            position: relative;
        }

        .weather-card p {
            opacity: 0.85;
            margin: 5px 0;
            z-index: 1;
            position: relative;
        }

        .weather-card .temp {
            font-size: 3rem;
            font-weight: 700;
            margin: 10px 0;
            z-index: 1;
            position: relative;
        }

        .weather-card .desc {
            font-size: 1.2rem;
            margin-bottom: 15px;
            z-index: 1;
            position: relative;
        }

        /* Weather metrics */
        .metrics {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }

        .metric {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 10px 15px;
            flex: 1;
            min-width: 80px;
            text-align: center;
        }

        .metric p {
            margin: 0;
            font-size: 0.9rem;
        }

        .metric .value {
            font-size: 1.2rem;
            font-weight: 600;
        }

        /* Daily forecast */
        .daily-forecast {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 15px 0;
        }

        .forecast-day {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 15px;
            min-width: 100px;
            text-align: center;
            flex: 1;
        }

        .forecast-day .day {
            font-size: 1rem;
            margin-bottom: 10px;
        }

        .forecast-day .icon {
            font-size: 1.8rem;
            margin: 10px 0;
        }

        .forecast-day .temp {
            font-size: 1.3rem;
            font-weight: 600;
        }

        /* Custom selectbox */
        div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.15) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
            color: white !important;
            padding: 10px !important;
        }

        div[data-baseweb="select"] svg {
            color: white !important;
        }

        div[data-baseweb="select"] input {
            color: white !important;
        }

        /* Custom button */
        button[kind="primary"] {
            background: linear-gradient(45deg, #5D26C1, #a17fe0) !important;
            border: none !important;
            padding: 12px 30px !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(93, 38, 193, 0.4) !important;
        }

        button[kind="primary"]:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 20px rgba(93, 38, 193, 0.6) !important;
        }

        /* Charts styling */
        .plot-container {
            border-radius: 16px !important;
            overflow: hidden !important;
        }

        /* Weather icon pulsar effect */
        .weather-icon {
            position: relative;
            font-size: 3rem;
            margin: 10px 0;
            z-index: 1;
        }

        .icon-pulsar {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            z-index: -1;
            animation: iconPulse 3s infinite;
        }

        @keyframes iconPulse {
            0% {transform: translate(-50%, -50%) scale(0.8); opacity: 0.8;}
            50% {transform: translate(-50%, -50%) scale(1.2); opacity: 0.2;}
            100% {transform: translate(-50%, -50%) scale(0.8); opacity: 0.8;}
        }

        /* Hide hamburger menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Custom table styling */
        .styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            font-size: 0.9rem;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        .styled-table thead tr {
            background: linear-gradient(45deg, #5D26C1, #a17fe0);
            color: white;
            text-align: left;
            font-weight: bold;
        }

        .styled-table th,
        .styled-table td {
            padding: 15px;
        }

        .styled-table tbody tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            color: white;
        }

        .styled-table tbody tr:last-of-type {
            border-bottom: 2px solid #5D26C1;
        }

        .styled-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        /* New weekly summary card */
        .weekly-summary-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-around;
            color: white;
        }

        .summary-item {
            text-align: center;
            padding: 10px;
        }

        .summary-item .title {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 5px;
        }

        .summary-item .value {
            font-size: 2rem;
            font-weight: 700;
        }

        .summary-item .unit {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        /* Weekly forecast table */
        .weekly-forecast {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 12px;
            overflow: hidden;
            margin: 20px 0;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        .weekly-forecast th {
            background: linear-gradient(45deg, #5D26C1, #a17fe0);
            color: white;
            text-align: center;
            padding: 15px;
            font-weight: bold;
        }

        .weekly-forecast td {
            background: rgba(255, 255, 255, 0.05);
            color: white;
            text-align: center;
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .weekly-forecast tr:last-child td {
            border-bottom: none;
        }

        .weekly-forecast .weather-icon-cell {
            font-size: 1.8rem;
        }

        /* Loading animation */
        .loader {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
        }

        .loading-animation {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            border-top-color: #5D26C1;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to {transform: rotate(360deg);}
        }

        /* Responsive adjustments */
        @media screen and (max-width: 768px) {
            .header h1 {
                font-size: 2.5rem;
            }

            .metrics {
                flex-direction: column;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def show_weather_page():
    """Main function to display the weather page content"""
    # Apply CSS styles
    apply_weather_css()

    # Main header
    st.markdown("""
    <div class="header">
        <h1>🌤️ O'zbekiston Ob-havo AURA</h1>
        <p>Real vaqtda ob-havo ma'lumotlari, haftalik prognoz va tahlillar</p>
    </div>
    """, unsafe_allow_html=True)

    # Create a container for the main content
    main_container = st.container()

    with main_container:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            region = st.selectbox("Viloyatni tanlang", list(UZB_CITIES.keys()), index=0)
            search_btn = st.button("🔍 Ob-havo ma'lumotlarini ko'rish", use_container_width=True)

        if search_btn or 'last_region' in st.session_state:
            # Store last selected region in session state
            if search_btn:
                st.session_state.last_region = region
            else:
                region = st.session_state.last_region

            with st.spinner("Ma'lumotlar yuklanmoqda..."):
                # Loading animation
                st.markdown("""
                <div class="loader">
                    <div class="loading-animation"></div>
                </div>
                """, unsafe_allow_html=True)

                # Small delay for animation effect
                time.sleep(1)

                # Get weather data
                weather_data = show_weather(region)
                forecast_data = get_forecast(region)

                if weather_data and forecast_data:
                    temp = weather_data["temp"]
                    feels_like = weather_data["feels_like"]
                    humidity = weather_data["humidity"]
                    wind_speed = weather_data["wind_speed"]
                    pressure = weather_data["pressure"]
                    rain_chance = weather_data["rain_chance"]
                    description = weather_data["description"]
                    icon_code = weather_data["icon"]
                    date = weather_data["date"]
                    lat = weather_data["lat"]
                    lon = weather_data["lon"]

                    # Weather icon from our mapping
                    weather_emoji = WEATHER_ICONS.get(icon_code, "🌤️")
                    weather_color = WEATHER_COLORS.get(icon_code, "#90CDF4")

                    # Create main layout
                    row1_col1, row1_col2 = st.columns([1, 2])

                    # Current weather card
                    with row1_col1:
                        st.markdown(f"""
                        <div class="weather-card" style="background: linear-gradient(45deg, {weather_color}, {weather_color}aa);">
                            <div class="pulse"></div>
                            <h2>{region}</h2>
                            <p>O'zbekiston | {date}</p>
                            <div class="weather-icon">
                                {weather_emoji}
                                <div class="icon-pulsar"></div>
                            </div>
                            <div class="temp">{temp}°C</div>
                            <div class="desc">{description}</div>
                            <div class="metrics">
                                <div class="metric">
                                    <p>His qilinishi</p>
                                    <div class="value">{feels_like}°C</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Additional metrics as cards
                        st.markdown("""
                        <div class="glass-card">
                            <h3>Havo holati tafsilotlari</h3>
                            <div class="metrics">
                        """, unsafe_allow_html=True)

                        # Add weather metrics
                        metrics_html = f"""
                            <div class="metric">
                                <p>Namlik</p>
                                <div class="value">{humidity}%</div>
                            </div>
                            <div class="metric">
                                <p>Shamol</p>
                                <div class="value">{wind_speed} m/s</div>
                            </div>
                            <div class="metric">
                                <p>Bosim</p>
                                <div class="value">{pressure} hPa</div>
                            </div>
                        """
                        st.markdown(metrics_html + "</div></div>", unsafe_allow_html=True)

                    # Map in the second column
                    with row1_col2:
                        st.markdown("""
                        <div class="glass-card">
                            <h3>📍 Joylashuv</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        # Create a map centered at the city's coordinates
                        m = folium.Map(location=[lat, lon], zoom_start=10)

                        # Add a marker for the city
                        tooltip = f"{region}: {temp}°C, {description}"
                        folium.Marker(
                            [lat, lon],
                            popup=f"{region}<br>{temp}°C<br>{description}",
                            tooltip=tooltip,
                            icon=folium.Icon(color="red", icon="info-sign")
                        ).add_to(m)

                        # Display the map
                        folium_static(m)

                    # Weekly Average Summary
                    st.markdown("""
                    <div class="glass-card">
                        <h3>📊 Haftalik O'rtacha Ko'rsatkichlar</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Weekly average summary
                    weekly_avg_temp = forecast_data["weekly_avg_temp"]
                    weekly_avg_rain_prob = forecast_data["weekly_avg_rain_prob"]

                    st.markdown(f"""
                    <div class="weekly-summary-card">
                        <div class="summary-item">
                            <div class="title">O'rtacha Harorat</div>
                            <div class="value">{weekly_avg_temp}<span class="unit">°C</span></div>
                        </div>
                        <div class="summary-item">
                            <div class="title">O'rtacha Yog'ingarchilik Ehtimoli</div>
                            <div class="value">{weekly_avg_rain_prob}<span class="unit">%</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Weekly Forecast Table
                    st.markdown("""
                    <div class="glass-card">
                        <h3>📅 Haftalik Prognoz Jadvali</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create weekly forecast table
                    weekly_table_html = """
                    <table class="weekly-forecast">
                        <thead>
                            <tr>
                                <th>Kun</th>
                                <th>Sana</th>
                                <th>Ob-havo</th>
                                <th>Harorat</th>
                                <th>Yog'ingarchilik</th>
                                <th>Shamol</th>
                                <th>Namlik</th>
                            </tr>
                        </thead>
                        <tbody>
                    """

                    for i, date in enumerate(forecast_data["daily_dates"]):
                        day_name = date.strftime("%a")
                        date_str = date.strftime("%d-%m")
                        temp = forecast_data["daily_temps"][i]
                        icon = forecast_data["daily_icons"][i]
                        rain_prob = forecast_data["daily_rain_probs"][i]
                        wind_speed = forecast_data["daily_wind_speeds"][i]
                        humidity = forecast_data["daily_humidities"][i]

                        weather_emoji = WEATHER_ICONS.get(icon, "🌤️")

                        weekly_table_html += f"""
                        <tr>
                            <td>{day_name}</td>
                            <td>{date_str}</td>
                            <td class="weather-icon-cell">{weather_emoji}</td>
                            <td>{temp}°C</td>
                            <td>{round(rain_prob)}%</td>
                            <td>{round(wind_speed, 1)} m/s</td>
                            <td>{humidity}%</td>
                        </tr>
                        """

                    weekly_table_html += """
                        </tbody>
                    </table>
                    """

                    st.markdown(weekly_table_html, unsafe_allow_html=True)

                    # Temperature forecast charts
                    st.markdown("""
                    <div class="glass-card">
                        <h3>🌡️ Harorat prognozi (Har 3 soatlik)</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create temperature chart data
                    dates_str = [date.strftime("%d-%m %H:%M") for date in forecast_data["dates"][:20]]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=dates_str,
                        y=forecast_data["temps"][:20],
                        mode='lines+markers',
                        name='Harorat',
                        line=dict(color='#FF9500', width=3),
                        marker=dict(size=8),
                        hovertemplate='%{y}°C'
                    ))

                    # Layout for the temperature chart
                    fig.update_layout(
                        title="Har 3 soatlik harorat prognozi",
                        xaxis_title="Sana/Vaqt",
                        yaxis_title="Harorat (°C)",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        hovermode="x unified",
                        xaxis=dict(
                            tickangle=-45,
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)'
                        )
                    )

                    # Display the plotly chart
                    st.plotly_chart(fig, use_container_width=True)

                    # Precipitation forecast chart
                    st.markdown("""
                    <div class="glass-card">
                        <h3>🌧️ Yog'ingarchilik ehtimoli (5 kun)</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create precipitation chart
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        x=dates_str,
                        y=forecast_data["rain_probs"][:20],
                        name='Yog\'ingarchilik',
                        marker_color='#3182CE',
                        hovertemplate='%{y}%'
                    ))

                    # Layout for precipitation chart
                    fig2.update_layout(
                        title="5 kunlik yog'ingarchilik ehtimoli",
                        xaxis_title="Sana/Vaqt",
                        yaxis_title="Ehtimollik (%)",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis=dict(
                            tickangle=-45,
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)',
                            range=[0, 100]  # Fixed range for percentage
                        )
                    )

                    # Display the precipitation chart
                    st.plotly_chart(fig2, use_container_width=True)

                    # Humidity and Wind comparison
                    st.markdown("""
                    <div class="glass-card">
                        <h3>💨 Shamol va Namlik taqqoslash (5 kun)</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create humidity and wind speed chart (dual axis)
                    fig3 = go.Figure()

                    # Add humidity trace
                    fig3.add_trace(go.Scatter(
                        x=dates_str,
                        y=forecast_data["humidities"][:20],
                        name='Namlik',
                        mode='lines+markers',
                        line=dict(color='#38B2AC', width=3),
                        marker=dict(size=6),
                        hovertemplate='%{y}%'
                    ))

                    # Add wind speed trace
                    fig3.add_trace(go.Scatter(
                        x=dates_str,
                        y=forecast_data["wind_speeds"][:20],
                        name='Shamol tezligi',
                        mode='lines+markers',
                        line=dict(color='#ED8936', width=3, dash='dot'),
                        marker=dict(size=6),
                        hovertemplate='%{y} m/s',
                        yaxis='y2'
                    ))

                    # Layout for the dual axis chart
                    fig3.update_layout(
                        title="Shamol tezligi va namlik taqqoslash",
                        xaxis_title="Sana/Vaqt",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        hovermode="x unified",
                        xaxis=dict(
                            tickangle=-45,
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            title="Namlik (%)",
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)',
                            range=[0, 100]
                        ),
                        yaxis2=dict(
                            title="Shamol tezligi (m/s)",
                            overlaying='y',
                            side='right',
                            range=[0, max(forecast_data["wind_speeds"][:20]) * 1.2]
                        )
                    )

                    # Display the dual axis chart
                    st.plotly_chart(fig3, use_container_width=True)

                    # Display additional weather information
                    st.markdown("""
                    <div class="glass-card">
                        <h3>ℹ️ Qo'shimcha ma'lumotlar</h3>
                        <p>Ob-havo ma'lumotlari OpenWeatherMap API orqali olingan. Eng so'nggi yangilanish vaqti: {}</p>
                    </div>
                    """.format(datetime.now().strftime("%d-%m-%Y %H:%M")), unsafe_allow_html=True)

                else:
                    st.error(
                        f"{region} uchun ob-havo ma'lumotlarini olishda xatolik yuz berdi. Iltimos, boshqa viloyatni tanlang yoki keyinroq qayta urinib ko'ring.")


if __name__ == "__main__":
    show_weather_page()