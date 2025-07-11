import streamlit as st
import os
import requests # For Open-Meteo API
from dotenv import load_dotenv
import datetime # For formatting dates
import openai # For OpenAI API

# Load environment variables from .env file
load_dotenv()

# --- OpenAI API Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
OPENAI_AVAILABLE = False

if OPENAI_API_KEY:
    try:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        # You can add a test call here if needed, e.g., list models, but it might incur costs or slow down startup.
        # st.success("OpenAI client configured successfully.")
    except Exception as e:
        st.error(f"Error configuring OpenAI client: {e}")
        openai_client = None
        OPENAI_AVAILABLE = False
else:
    st.warning("""
    OpenAI API key not found.
    Please create a `.env` file in the root directory and add your API key like this:
    `OPENAI_API_KEY="YOUR_API_KEY_HERE"`
    The app will use mocked responses for AI features.
    """)

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

# --- ISRIC SoilGrids API Functions ---
def get_soil_data(latitude, longitude):
    """
    Fetches soil data from ISRIC SoilGrids REST API for a given latitude and longitude.
    Retrieves properties like pH, organic carbon, clay/sand/silt content, CEC, and bulk density.
    """
    if latitude is None or longitude is None:
        return None

    # Define the properties and depths we are interested in
    # Properties: phh2o, soc, clay, sand, silt, cec, bdod
    # Depths: 0-5cm (or a suitable single depth)
    # ISRIC uses specific naming for depths, e.g., 0-5cm is "0-5cm", 5-15cm is "5-15cm"
    # For simplicity, we'll target a common surface layer, e.g., 0-30cm if available or average of top layers.
    # The REST API seems to prefer querying one property at a time or specific layers.
    # Let's try to get a few key properties at a common topsoil depth.
    # Documentation: https://rest.soilgrids.org/soilgrids/v2.0/docs #/default/query_layer_query_layer_get

    base_url = "https://rest.soilgrids.org/soilgrids/v2.0/properties/query"
    properties_to_fetch = {
        "phh2o": "pH water",
        "soc": "Soil Organic Carbon",
        "clay": "Clay Content",
        "sand": "Sand Content",
        "silt": "Silt Content",
        "cec": "Cation Exchange Capacity",
        "bdod": "Bulk Density"
    }
    depth_interval = "0-30cm_mean" # Example: mean value for 0-30cm depth. Or use "0-5cm_mean", "5-15cm_mean" etc.
                                 # The API expects specific depth intervals like "d_0_5", "d_5_15" etc.
                                 # Let's use specific layers and take the mean of the top ones if direct 0-30cm is not simple.
                                 # The API allows querying for depths like '0-5cm', '5-15cm', '15-30cm'.
                                 # We will query for these and report them.

    soil_results = {}

    # ISRIC API expects lon, lat order for point queries
    params = {
        "lon": longitude,
        "lat": latitude,
        "depth_interval": "0-30cm", # This seems to be a valid interval for some queries
    }

    common_layers = ["0-5cm", "5-15cm", "15-30cm"] # Depths as per SoilGrids convention for "depths" parameter

    for prop_code, prop_name in properties_to_fetch.items():
        params_prop = {
            "lon": longitude,
            "lat": latitude,
            "property": prop_code,
            "depth": common_layers, # Request multiple depths
            "value": "mean" # Request the mean value for the layers
        }
        try:
            response = requests.get(base_url, params=params_prop)
            response.raise_for_status()
            data = response.json()

            # st.json(data) # For debugging the structure

            if "properties" in data and "layers" in data["properties"]:
                # Extract values for each depth and store them
                # The API returns values in the order of depths requested
                layer_values = {}
                for layer_info in data["properties"]["layers"]:
                    if layer_info["name"] == prop_code:
                        for i, depth_label_obj in enumerate(layer_info["depths"]):
                            depth_label = depth_label_obj["label"]
                            # Correctly access the mapped value, which might be under a "values" dict with "mean"
                            value_data = layer_info["values"]["mean"] # if value="mean" was requested
                            if i < len(value_data): # Ensure index exists
                                # SoilGrids values are often multiplied by a factor (e.g., pH by 10, OC by 10 g/kg)
                                # We need to convert them to standard units based on their documentation.
                                val = value_data[i]
                                if val is None: # Skip if value is None (e.g. water body)
                                    continue

                                converted_val = val
                                unit = ""
                                if prop_code == "phh2o": # pH x 10
                                    converted_val = val / 10.0
                                    unit = ""
                                elif prop_code == "soc": #  g/kg (needs conversion factor if it's dg/kg or cg/kg)
                                                     # SoilGrids provides soc in dg/kg. To get g/kg, divide by 10.
                                                     # To get %, divide g/kg by 10. So dg/kg to % is divide by 100.
                                    converted_val = val / 100.0 # dg/kg to %
                                    unit = "%"
                                elif prop_code in ["clay", "sand", "silt"]: # g/100g (already percentage)
                                    converted_val = val / 10.0 # If values are in g/kg, convert to % (g/100g)
                                    unit = "%"
                                elif prop_code == "cec": # cmol(c)/kg (pH 7)
                                    converted_val = val / 10.0 # If in mmol(c)/kg, convert to cmol(c)/kg
                                    unit = "cmol(c)/kg"
                                elif prop_code == "bdod": # cg/cm3. To get g/cm3 divide by 100
                                    converted_val = val / 100.0
                                    unit = "g/cm³"

                                layer_values[depth_label] = f"{converted_val:.2f} {unit}".strip()
                        soil_results[prop_name] = layer_values
            else:
                soil_results[prop_name] = "Not found or error in response structure"

        except requests.exceptions.RequestException as e:
            # st.error(f"Error fetching soil data for {prop_name}: {e}")
            soil_results[prop_name] = "API request failed"
        except Exception as e:
            # st.error(f"Unexpected error processing soil data for {prop_name}: {e}")
            soil_results[prop_name] = "Processing error"

    return soil_results if soil_results else None


def get_openai_response(prompt_text, model="gpt-3.5-turbo"):
    """
    Sends a prompt to the OpenAI API and returns the response.
    Uses a mocked response if the API is not available or if openai_client is None.
    """
    if OPENAI_AVAILABLE and openai_client:
        try:
            completion = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful agricultural advisor providing concise and practical advice."},
                    {"role": "user", "content": prompt_text}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"Error communicating with OpenAI API: {e}")
            return "OpenAI API Error: Could not retrieve a response." # Provide a fallback error message
    else:
        # This part should ideally not be reached if OPENAI_AVAILABLE is false from the main logic,
        # as the main logic checks OPENAI_AVAILABLE before calling this function.
        # This is a defensive fallback in case this function is called directly when it shouldn't be.
        return "OpenAI client is not available. Please ensure the API key is correctly configured. (This is a fallback message from get_openai_response)"

def main():
    st.set_page_config(page_title="AgriGuru Chat", layout="wide")

    st.title("🌾 AgriGuru: Your Agricultural Advisory Chatbot")

    # Initialize session state for chat messages and user location if they don't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_location" not in st.session_state:
        st.session_state.user_location = "" # Initialize user_location

    # Sidebar for location input
    with st.sidebar:
        st.header("Your Location")
        current_location_placeholder = "Not set"
        if st.session_state.user_location:
            current_location_placeholder = st.session_state.user_location

        loc_input = st.text_input("Enter your Village/Town, District:", value=st.session_state.user_location, key="location_input_field")
        if st.button("Set Location", key="set_location_button"):
            if loc_input:
                st.session_state.user_location = loc_input
                st.success(f"Location set to: {st.session_state.user_location}")
            else:
                st.warning("Please enter a location.")

        st.caption(f"Current context location: {current_location_placeholder}")
        st.markdown("---")
        st.info("Ask AgriGuru anything about farming!")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- This is where the new AI query processing logic will go ---
        # For now, just a placeholder response
        with st.chat_message("assistant"):
            response = ""
            if not st.session_state.user_location:
                response = "Please set your location in the sidebar first so I can provide more relevant advice."
                st.markdown(response) # Show the "Please set location" message
            else:
                # Main query processing logic starts here
                user_query = prompt.lower() # For keyword matching
                context_for_ai = f"User is in location: {st.session_state.user_location}. User's query: \"{prompt}\"\n"
                api_data_summary = ""

                with st.spinner("Gathering information..."):
                    # --- Weather Data Fetch ---
                    if "weather" in user_query or "temperature" in user_query or "forecast" in user_query or "rain" in user_query:
                        lat, lon, loc_name = get_coordinates_for_location(st.session_state.user_location)
                        if lat and lon:
                            weather_data = get_weather_forecast(lat, lon)
                            if weather_data:
                                current_weather_desc = "Weather data unavailable."
                                if "current" in weather_data:
                                    current = weather_data["current"]
                                    weather_code_desc = WEATHER_CODES.get(current.get("weather_code"), "N/A")
                                    current_weather_desc = (
                                        f"Current weather in {loc_name}: {current.get('temperature_2m')}°C, "
                                        f"{weather_code_desc}, Wind: {current.get('wind_speed_10m')} km/h."
                                    )
                                api_data_summary += current_weather_desc + "\n"
                            else:
                                api_data_summary += f"Could not fetch current weather data for {st.session_state.user_location}.\n"
                        else:
                            api_data_summary += f"Could not find coordinates for weather for {st.session_state.user_location}.\n"

                    # --- Soil Data Fetch ---
                    if "soil" in user_query or "ph" in user_query or "clay" in user_query or "sand" in user_query or "organic carbon" in user_query:
                        # Attempt to get coordinates again if not already fetched for weather (can be optimized)
                        lat, lon, loc_name = get_coordinates_for_location(st.session_state.user_location) # Ensure loc_name is from here for soil context
                        if lat and lon:
                            soil_data = get_soil_data(lat, lon)
                            if soil_data:
                                soil_summary = f"Estimated soil properties for {loc_name}:\n"
                                for prop, values_at_depths in soil_data.items():
                                    if isinstance(values_at_depths, dict) and values_at_depths:
                                        soil_summary += f"  {prop}:\n"
                                        for depth, value in values_at_depths.items():
                                            soil_summary += f"    {depth}: {value}\n"
                                    elif isinstance(values_at_depths, str): # Error message for a property
                                        soil_summary += f"  {prop}: {values_at_depths}\n"
                                api_data_summary += soil_summary
                            else:
                                api_data_summary += f"Could not fetch soil data for {st.session_state.user_location}.\n"
                        else:
                            api_data_summary += f"Could not find coordinates for soil data for {st.session_state.user_location}.\n"

                    # --- Market Data (USDA - if user specifically asks for US data or certain keywords) ---
                    # This part is kept separate as it's US-specific and might not always be relevant
                    # For Indian market insights, we will rely on OpenAI's general knowledge combined with location.
                    if "usda" in user_query or ("market price" in user_query and ("united states" in user_query or "us market" in user_query)):
                        # A more sophisticated keyword extraction for commodity and year would be needed here
                        # For now, this is just a placeholder to show where it would fit.
                        # Example: if user says "USDA price for corn in Iowa 2023"
                        # commodity_match = re.search(r"(\w+)\s*(?:price|market)", user_query) # etc.
                        # For now, we won't automatically call USDA unless explicitly asked in a very specific way.
                        # The general market queries will be handled by OpenAI using the Indian location context.
                        pass # Not implementing automatic USDA calls from general chat for now.

                if api_data_summary:
                    context_for_ai += "\nContextual Information from APIs:\n" + api_data_summary.strip() + "\n"
                else:
                    context_for_ai += "\nNo specific API data was automatically fetched for this query. Please rely on general knowledge.\n"

                final_prompt_to_ai = (
                    f"{context_for_ai}\n"
                    "You are AgriGuru, an intelligent agricultural advisory chatbot. "
                    "Based on the user's query and the provided contextual information (if any), "
                    "give a helpful and comprehensive answer. If specific live data (like exact soil composition or "
                    "hyper-local market prices for the user's village) is not available in the provided context, "
                    "use your general knowledge to provide the best possible advice for the user's location and query. "
                    "If you are using general knowledge for specifics like market prices or detailed soil data, "
                    "you can briefly state that the information is based on general trends or typical conditions for the region if precise local data wasn't fetched."
                )

                # st.info(f"DEBUG: Final prompt to AI:\n{final_prompt_to_ai}") # For debugging

                if OPENAI_AVAILABLE:
                    with st.spinner("AgriGuru is thinking..."):
                        ai_response_content = get_openai_response(final_prompt_to_ai)
                        st.markdown(ai_response_content)
                        response = ai_response_content # To be added to history
                else:
                    response = "OpenAI API key is not available. Cannot process your query with AI. (Mocked: Query understood, but AI is offline)"
                    st.warning(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
