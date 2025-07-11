import streamlit as st
import google.generativeai as genai
import os
import requests # For Open-Meteo API
from dotenv import load_dotenv
import datetime # For formatting dates

# Load environment variables from .env file
load_dotenv()

# --- Gemini Pro API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        GEMINI_AVAILABLE = True
    except Exception as e:
        st.error(f"Error configuring Gemini API: {e}")
        gemini_model = None
        GEMINI_AVAILABLE = False
else:
    st.warning("""
    Gemini API key not found.
    Please create a `.env` file in the root directory and add your API key like this:
    `GEMINI_API_KEY="YOUR_API_KEY_HERE"`
    The app will use mocked responses for AI features.
    """)
    gemini_model = None
    GEMINI_AVAILABLE = False

# --- USDA NASS API Configuration & Functions ---
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_API_AVAILABLE = bool(USDA_API_KEY)

def get_usda_market_data(commodity_name, year, state_alpha=None):
    """
    Fetches market data from USDA NASS Quick Stats API.
    Focuses on 'PRICE RECEIVED' for a given commodity, year, and optionally state.
    Example commodity_name: "CORN", "SOYBEANS", "WHEAT"
    Example year: "2023"
    Example state_alpha: "IA" (for Iowa)
    """
    if not USDA_API_AVAILABLE:
        st.error("USDA API Key not configured. Please add it to your .env file.")
        return None

    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        "key": USDA_API_KEY,
        "format": "JSON",
        "commodity_desc": commodity_name.upper(),
        "year": str(year),
        "statisticcat_desc": "PRICE RECEIVED", # Focus on price received by farmers
        # "agg_level_desc": "NATIONAL" # Default to National level
    }
    # Example: data_item = "CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"
    # We might need to be more specific with data_item or parse what's available.
    # For simplicity, we'll try to get all price received data for the commodity and filter.

    if state_alpha:
        params["state_alpha"] = state_alpha.upper()
        # params["agg_level_desc"] = "STATE" # For state-level data

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if "data" in data and len(data["data"]) > 0:
            # Further parsing might be needed depending on the exact data structure for different commodities
            # This is a simplified example; the API can return many detailed series.
            # We'll try to find a relevant value.
            # st.write(data["data"]) # For debugging

            results = []
            for item in data["data"]:
                value = item.get("Value")
                unit = item.get("unit_desc")
                period = item.get("period_desc")
                domain_desc = item.get("domain_desc") # e.g., "TOTAL", "ORGANIC STATUS"
                statisticcat_desc = item.get("statisticcat_desc")

                # Filter for "PRICE RECEIVED" and non-empty values
                if statisticcat_desc == "PRICE RECEIVED" and value and value.strip() != "(D)": # (D) means withheld
                    results.append({
                        "value": value,
                        "unit": unit,
                        "period": period,
                        "description": item.get("short_desc"),
                        "domain": domain_desc,
                        "state": item.get("state_name", "NATIONAL")
                    })
            return results
        elif "error" in data:
            st.error(f"USDA API Error: {data['error']}")
            return None
        else:
            st.info(f"No specific 'PRICE RECEIVED' data found for {commodity_name} in {year} {('for state ' + state_alpha) if state_alpha else 'at national level'}. The API might return other related stats, or the query needs refinement.")
            # st.json(data) # Option to show raw data if nothing specific is found
            return [] # Return empty list if no data field or empty data

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching USDA market data: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred with USDA data: {e}")
        return None


# --- Open-Meteo Weather API Functions ---
def get_coordinates_for_location(location_name):
    """Geocodes a location name to latitude and longitude using Open-Meteo Geocoding API."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1&language=en&format=json"
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data and "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"], data["results"][0].get("name", location_name)
        else:
            return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error geocoding location: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"An unexpected error occurred during geocoding: {e}")
        return None, None, None

def get_weather_forecast(latitude, longitude):
    """Fetches weather forecast from Open-Meteo."""
    if latitude is None or longitude is None:
        return None
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching weather: {e}")
        return None

# Basic weather code descriptions (can be expanded)
WEATHER_CODES = {
    0: "☀️ Clear sky",
    1: "🌤️ Mainly clear",
    2: "🌥️ Partly cloudy",
    3: "☁️ Overcast",
    45: "🌫️ Fog",
    46: "🌫️ Depositing rime fog",
    51: "💧 Drizzle: Light intensity",
    53: "💧 Drizzle: Moderate intensity",
    55: "💧 Drizzle: Dense intensity",
    56: "❄️ Freezing Drizzle: Light intensity",
    57: "❄️ Freezing Drizzle: Dense intensity",
    61: "🌧️ Rain: Slight intensity",
    63: "🌧️ Rain: Moderate intensity",
    65: "🌧️ Rain: Heavy intensity",
    66: "❄️ Freezing Rain: Light intensity",
    67: "❄️ Freezing Rain: Heavy intensity",
    71: "🌨️ Snow fall: Slight intensity",
    73: "🌨️ Snow fall: Moderate intensity",
    75: "🌨️ Snow fall: Heavy intensity",
    77: "❄️ Snow grains",
    80: "🌦️ Rain showers: Slight intensity",
    81: "🌦️ Rain showers: Moderate intensity",
    82: "⛈️ Rain showers: Violent intensity",
    85: "🌨️ Snow showers: Slight intensity",
    86: "🌨️ Snow showers: Heavy intensity",
    95: " thunderstorms", # Further specification needed by client
    96: "⛈️ Thunderstorm with slight hail",
    99: "⛈️ Thunderstorm with heavy hail",
}

def get_gemini_response(prompt_text):
    """
    Sends a prompt to Gemini Pro and returns the response.
    Uses a mocked response if the API is not available.
    """
    if GEMINI_AVAILABLE and gemini_model:
        try:
            response = gemini_model.generate_content(prompt_text)
            return response.text
        except Exception as e:
            return f"Error communicating with Gemini API: {e}"
    else:
        # Mocked response
        if "crop recommendation" in prompt_text.lower():
            return "Mocked response: Based on your input, consider planting Tomatoes or Corn."
        elif "weather forecast" in prompt_text.lower():
            return "Mocked response: Sunny with a high of 25°C."
        elif "market insights" in prompt_text.lower():
            return "Mocked response: Prices for Wheat are currently stable."
        elif "sustainable farming" in prompt_text.lower():
            return "Mocked response: Consider using cover crops and no-till farming."
        else:
            return "Mocked response: Unable to generate a response for this query."

def main():
    st.set_page_config(page_title="AgriGuru", layout="wide")

    st.title("🌾 AgriGuru: Intelligent Agricultural Advisory System")
    st.caption("Your AI-powered assistant for smarter farming decisions.")

    # Placeholder for different sections
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Crop Recommendations", "Weather Forecast", "Market Insights", "Sustainable Farming Practices"])

    if page == "Crop Recommendations":
        st.header("🌱 Crop Recommendations")
        st.write("Get personalized crop recommendations based on your local conditions.")

        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Enter your location (e.g., city, region):", key="crop_location")
        with col2:
            soil_type = st.selectbox(
                "Select soil type:",
                ["Loamy", "Sandy", "Clay", "Silty", "Peaty", "Chalky"],
                key="soil_type"
            )

        # Placeholder for more specific data inputs (simulating satellite/sensor data)
        st.subheader("Optional: Additional Data")
        col3, col4 = st.columns(2)
        with col3:
            avg_rainfall = st.slider("Average Annual Rainfall (mm):", 0, 4000, 1000, key="avg_rainfall")
        with col4:
            avg_temp = st.slider("Average Growing Season Temperature (°C):", -10, 40, 20, key="avg_temp")

        if st.button("Get Crop Recommendations", key="crop_rec_button"):
            if location:
                prompt = f"Provide crop recommendations for a location like {location} with {soil_type} soil. Average annual rainfall is {avg_rainfall}mm and average growing season temperature is {avg_temp}°C. Focus on suitability and yield."
                with st.spinner("Fetching recommendations..."):
                    recommendations = get_gemini_response(prompt)
                    st.subheader("Recommended Crops:")
                    st.markdown(recommendations)
            else:
                st.error("Please enter a location.")

    elif page == "Weather Forecast":
        st.header("🌦️ Weather Forecast")
        st.write("Access real-time weather forecasts for your region using Open-Meteo.")

        weather_location_input = st.text_input("Enter city or region for weather forecast:", key="weather_location_input")

        if st.button("Get Weather Forecast", key="weather_button"):
            if weather_location_input:
                with st.spinner(f"Fetching coordinates for {weather_location_input}..."):
                    lat, lon, loc_name = get_coordinates_for_location(weather_location_input)

                if lat and lon:
                    st.write(f"Found coordinates for {loc_name}: Latitude {lat:.2f}, Longitude {lon:.2f}")
                    with st.spinner(f"Fetching weather forecast for {loc_name}..."):
                        forecast_data = get_weather_forecast(lat, lon)

                    if forecast_data:
                        st.subheader(f"Weather Forecast for {loc_name}")

                        # Display Current Weather
                        if "current" in forecast_data:
                            current = forecast_data["current"]
                            current_weather_desc = WEATHER_CODES.get(current.get("weather_code"), "N/A")
                            st.markdown(f"**Now:** {current.get('temperature_2m')}°C, {current_weather_desc}, Wind: {current.get('wind_speed_10m')} km/h")

                        # Display Daily Forecast
                        if "daily" in forecast_data:
                            st.markdown("**7-Day Forecast:**")
                            daily = forecast_data["daily"]
                            # Create a simpler table-like display
                            header = "| Date       | Max Temp (°C) | Min Temp (°C) | Precipitation (mm) | Condition         |"
                            separator = "|------------|---------------|---------------|--------------------|-------------------|"
                            st.markdown(header)
                            st.markdown(separator)

                            for i in range(len(daily.get("time", []))):
                                try:
                                    date_str = daily["time"][i]
                                    # Attempt to parse different date formats Open-Meteo might send
                                    try:
                                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%a, %b %d')
                                    except ValueError:
                                        date_obj = date_str # Keep original if parsing fails

                                    max_temp = daily["temperature_2m_max"][i]
                                    min_temp = daily["temperature_2m_min"][i]
                                    precip = daily["precipitation_sum"][i]
                                    condition_code = daily["weather_code"][i]
                                    condition_desc = WEATHER_CODES.get(condition_code, "N/A")

                                    row = f"| {date_obj:<10} | {max_temp:<13.1f} | {min_temp:<13.1f} | {precip:<18.1f} | {condition_desc:<17} |"
                                    st.markdown(row)
                                except IndexError:
                                    st.caption(f"Could not display full data for day {i+1}")
                                except Exception as e:
                                    st.caption(f"Error processing daily forecast entry: {e}")
                        else:
                            st.write("Daily forecast data not available.")
                    else:
                        st.error("Could not retrieve weather forecast data.")
                else:
                    st.error(f"Could not find coordinates for '{weather_location_input}'. Please try a different location name.")
            else:
                st.error("Please enter a location for the weather forecast.")

    elif page == "Market Insights":
        st.header("📈 Market Insights (USDA Data - US Only)")
        st.write("Access agricultural market price information from the USDA NASS Quick Stats API.")

        if not USDA_API_AVAILABLE:
            st.warning("USDA API Key not found in `.env` file. This section requires a valid API key from USDA NASS to function. Market insights from Gemini will be used as a fallback if available.")

        # Common US commodities for easier selection
        common_commodities = ["CORN", "SOYBEANS", "WHEAT", "COTTON", "RICE", "SORGHUM", "BARLEY", "OATS", "APPLES", "GRAPES", "POTATOES", "CATTLE", "HOGS", "CHICKENS"]

        col1, col2, col3 = st.columns(3)
        with col1:
            commodity_name = st.selectbox("Select or type Commodity:", options=[""] + common_commodities, key="usda_commodity", format_func=lambda x: "Select Commodity" if x == "" else x)
            if not commodity_name: # Allow free text entry if not selected from dropdown
                 commodity_name_input = st.text_input("Or Enter Commodity Name (e.g., CORN):", key="usda_commodity_text")
                 if commodity_name_input: commodity_name = commodity_name_input #
        with col2:
            current_year = datetime.datetime.now().year
            year = st.number_input("Enter Year:", min_value=1900, max_value=current_year + 1, value=current_year, key="usda_year")
        with col3:
            # List of US State abbreviations for dropdown
            us_states = ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
            state_alpha = st.selectbox("Select State (optional, for state-level data):", options=us_states, key="usda_state")

        if st.button("Get USDA Market Data", key="usda_market_button"):
            final_commodity_name = commodity_name_input if not commodity_name and commodity_name_input else commodity_name

            if final_commodity_name and year:
                if USDA_API_AVAILABLE:
                    with st.spinner(f"Fetching market data for {final_commodity_name} ({year})..."):
                        market_data = get_usda_market_data(final_commodity_name, year, state_alpha if state_alpha else None)

                    if market_data:
                        st.subheader(f"USDA Price Data for {final_commodity_name.upper()} - {year} {('(' + state_alpha + ')' if state_alpha else '(National)')}")
                        if market_data: # Check if list is not empty
                            for entry in market_data:
                                st.markdown(f"- **{entry['description']}**: {entry['value']} {entry['unit']} (Period: {entry['period']}, Domain: {entry['domain']}, State: {entry['state']})")
                        else: # List is empty but not None (meaning API call was made but no specific data)
                             st.info(f"No specific 'PRICE RECEIVED' data found for {final_commodity_name} in {year} {('for state ' + state_alpha) if state_alpha else 'at national level'}. The API might return other related stats under different categories, or the query needs refinement for this specific commodity.")
                    elif market_data is None: # API call failed or key missing
                        st.error("Failed to retrieve data. Check API key or network.")
                    # else: market_data is an empty list, message already handled by get_usda_market_data or above

                elif GEMINI_AVAILABLE: # Fallback to Gemini if USDA key missing but Gemini is available
                    st.info("USDA API Key not available. Attempting to get general market insights using Gemini Pro...")
                    prompt = f"Provide general market insights for {final_commodity_name}"
                    if state_alpha:
                        prompt += f" in {state_alpha}"
                    prompt += f" for the year {year}."
                    with st.spinner("Fetching insights with Gemini..."):
                        insights = get_gemini_response(prompt)
                        st.subheader(f"General Market Insights for {final_commodity_name} (from Gemini):")
                        st.markdown(insights)
                else: # Neither API is available
                    st.error("Both USDA and Gemini API keys are unavailable. Cannot fetch market insights.")
            else:
                st.error("Please enter a commodity name and year.")

    elif page == "Sustainable Farming Practices":
        st.header("🌿 Sustainable Farming Practices")
        st.write("Learn about sustainable farming techniques and get advice.")

        sustainable_query = st.text_area("Ask a question about sustainable farming practices:", height=150, key="sustainable_query")

        if st.button("Get Sustainable Farming Advice", key="sustainable_button"):
            if sustainable_query:
                prompt = f"Regarding sustainable farming, what about: {sustainable_query}?"
                with st.spinner("Fetching advice..."):
                    advice = get_gemini_response(prompt)
                    st.subheader("Sustainable Farming Advice:")
                    st.markdown(advice)
            else:
                st.error("Please enter your question or topic.")

    st.sidebar.markdown("---")
    st.sidebar.info("Powered by AI and Data")

if __name__ == "__main__":
    main()
