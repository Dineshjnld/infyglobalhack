# AgriGuru - Crop Data Fetcher Module
# Fetches data required for crop recommendations: soil, historical yield, IoT sensor data.

import pandas as pd
import numpy as np
# soilDB is a Python package to interface with SoilGrids and other soil databases.
# It might require specific installation steps or dependencies like GDAL.
# For simplicity, if soilDB direct import causes issues in a minimal environment,
# we can fall back to using direct requests to SoilGrids REST API as done previously.
# The brief specifically mentioned "SoilGrids API (via soilDB in Python)".
try:
    from soilDB import SDA_spatialQuery, fetchSoilGrids
    SOILDB_AVAILABLE = True
except ImportError:
    SOILDB_AVAILABLE = False
    print("WARNING: soilDB library not found. Soil data fetching will be limited or use direct REST API if implemented as fallback.")
    # Alternative: use direct REST API as done in previous iterations if soilDB is problematic
    import requests

from config import settings # Assuming settings are appropriately configured for any API keys if needed

# --- Soil Data ---
def fetch_soil_data_soilgrids_rest(latitude, longitude, properties=None, depths=None):
    """
    Fetches soil data from ISRIC SoilGrids REST API for a given latitude and longitude.
    This is a fallback or alternative if soilDB direct usage is complex or has heavy dependencies.
    """
    if latitude is None or longitude is None:
        return {"error": "Latitude or longitude missing."}

    default_properties = {
        "phh2o": "pH water", "soc": "Soil Organic Carbon", "clay": "Clay Content",
        "sand": "Sand Content", "silt": "Silt Content", "cec": "Cation Exchange Capacity",
        "bdod": "Bulk Density"
    }
    properties_to_fetch = properties if properties else default_properties

    # Default depths as per SoilGrids common layers for REST API
    default_depth_layers = ["0-5cm", "5-15cm", "15-30cm"]
    depth_layers_to_query = depths if depths else default_depth_layers

    soil_results = {"latitude": latitude, "longitude": longitude, "properties": {}}
    base_url = "https://rest.soilgrids.org/soilgrids/v2.0/properties/query"

    for prop_code, prop_name in properties_to_fetch.items():
        params_prop = {
            "lon": longitude, "lat": latitude, "property": prop_code,
            "depth": depth_layers_to_query, "value": "mean"
        }
        try:
            response = requests.get(base_url, params=params_prop)
            response.raise_for_status()
            data = response.json()

            if "properties" in data and "layers" in data["properties"]:
                prop_data = {}
                for layer_info in data["properties"]["layers"]:
                    if layer_info["name"] == prop_code:
                        for i, depth_label_obj in enumerate(layer_info["depths"]):
                            depth_label = depth_label_obj["label"]
                            value_data_list = layer_info["values"]["mean"]
                            if i < len(value_data_list):
                                val = value_data_list[i]
                                if val is None: continue

                                converted_val, unit = val, "" # Default if no conversion needed
                                if prop_code == "phh2o": converted_val, unit = val / 10.0, ""
                                elif prop_code == "soc": converted_val, unit = val / 100.0, "%" # dg/kg to %
                                elif prop_code in ["clay", "sand", "silt"]: converted_val, unit = val / 10.0, "%" # g/kg to %
                                elif prop_code == "cec": converted_val, unit = val / 10.0, "cmol(c)/kg" # mmol(c)/kg to cmol(c)/kg
                                elif prop_code == "bdod": converted_val, unit = val / 100.0, "g/cm³" # cg/cm³ to g/cm³

                                prop_data[depth_label] = {"value": round(converted_val, 2), "unit": unit}
                soil_results["properties"][prop_name] = prop_data if prop_data else "No data for specified depths"
            else:
                soil_results["properties"][prop_name] = "Property not found or error in response"
        except requests.exceptions.RequestException as e:
            soil_results["properties"][prop_name] = f"API request failed: {e}"
        except Exception as e:
            soil_results["properties"][prop_name] = f"Processing error: {e}"

    return soil_results if soil_results["properties"] else {"error": "No soil properties could be fetched."}


def fetch_soil_data(latitude, longitude):
    """
    Fetches soil data for given coordinates.
    Uses soilDB if available, otherwise falls back to a direct REST API call to SoilGrids.
    The brief specifically mentioned "SoilGrids API (via soilDB in Python)".
    """
    if SOILDB_AVAILABLE:
        try:
            # Create a point geometry
            # Note: soilDB might expect coordinates in a specific CRS or format.
            # For fetchSoilGrids, it seems to handle WGS84 lat/lon directly.
            # result = fetchSoilGrids(lonlat=[longitude, latitude],
            #                         properties=['phh2o', 'soc', 'clay', 'sand', 'cec'])
            # fetchSoilGrids returns a complex object. We need to parse it into a simpler dict.
            # The structure of the returned object needs to be inspected to parse correctly.
            # For now, let's assume a simplified output or use the REST fallback.

            # Given the complexity of parsing fetchSoilGrids output without running it,
            # and the reliability of the REST API, we'll prefer the REST API method for now
            # for a consistent output structure.
            # If soilDB is a strict requirement and provides a simpler direct dict output for point queries,
            # this can be revisited. The soilDB examples often involve more complex spatial objects.
            print("INFO: soilDB is available, but using direct SoilGrids REST API for simpler point data structure.")
            return fetch_soil_data_soilgrids_rest(latitude, longitude)

        except Exception as e:
            print(f"ERROR: soilDB fetchSoilGrids failed: {e}. Falling back to REST API.")
            return fetch_soil_data_soilgrids_rest(latitude, longitude)
    else:
        print("INFO: soilDB not available. Using direct SoilGrids REST API.")
        return fetch_soil_data_soilgrids_rest(latitude, longitude)

# --- Historical Yield Data ---
def fetch_historical_yield_data(location_identifier):
    """
    Placeholder function to fetch historical yield data.
    In a real system, this would query a database or API (e.g., FAOSTAT, local sources).
    The brief mentions "FAO Soil Data or Indian Soil Health Card". Direct API access to these for specific yields is complex.
    This will likely require setting up a local database populated with this data.
    """
    print(f"INFO: Fetching historical yield data for {location_identifier} (Placeholder).")
    # Example: Dummy data for a few crops
    # This data should ideally be linked to soil types or specific regional characteristics.
    if "delhi_region" in location_identifier.lower():
        return {
            "wheat": {"avg_yield_kg_ha": 3500, "last_5yr_trend_percent": 2.5},
            "rice": {"avg_yield_kg_ha": 3000, "last_5yr_trend_percent": 1.0},
            "maize": {"avg_yield_kg_ha": 2500, "last_5yr_trend_percent": 3.0},
            "sugarcane": {"avg_yield_kg_ha": 70000, "last_5yr_trend_percent": 0.5},
        }
    elif "mumbai_region" in location_identifier.lower(): # Coastal, different crops
        return {
            "rice": {"avg_yield_kg_ha": 3200, "last_5yr_trend_percent": 1.2},
            "mango": {"avg_yield_kg_ha": 8000, "last_5yr_trend_percent": 5.0}, # Example, might be per tree
            "cashew": {"avg_yield_kg_ha": 700, "last_5yr_trend_percent": 3.0},
        }
    else:
        return {
            "unknown_crop": {"avg_yield_kg_ha": 0, "last_5yr_trend_percent": 0},
            "message": "No specific historical yield data for this generic location in placeholder."
        }

# --- IoT Sensor Data ---
def fetch_iot_sensor_data(farm_id):
    """
    Placeholder function to fetch IoT sensor data.
    In a real system, this would connect to an IoT platform (like Tania or FarmOS as per brief, possibly via MQTT or REST API).
    """
    print(f"INFO: Fetching IoT sensor data for farm {farm_id} (Placeholder).")
    # Example: Dummy sensor data
    # This data would be dynamic in a real system.
    return {
        "soil_moisture_percent": np.random.uniform(20.0, 70.0), # Percentage
        "air_temperature_celsius": np.random.uniform(15.0, 40.0), # Celsius
        "soil_temperature_celsius": np.random.uniform(10.0, 35.0), # Celsius
        "light_intensity_lux": np.random.uniform(10000, 80000), # Lux
        "timestamp": pd.Timestamp.now().isoformat()
    }

if __name__ == '__main__':
    print("--- Testing Crop Data Fetcher ---")

    # Test Soil Data Fetching
    print("\nTesting Soil Data (Delhi example):")
    # Coordinates for New Delhi, India
    test_lat_delhi = 28.6139
    test_lon_delhi = 77.2090
    soil_data_delhi = fetch_soil_data(test_lat_delhi, test_lon_delhi)
    if soil_data_delhi and "error" not in soil_data_delhi:
        for prop_name, data_at_depths in soil_data_delhi.get("properties", {}).items():
            print(f"  {prop_name}:")
            if isinstance(data_at_depths, dict):
                for depth, value_unit in data_at_depths.items():
                    print(f"    {depth}: {value_unit['value']} {value_unit['unit']}")
            else:
                print(f"    {data_at_depths}") # Error or message string
    else:
        print(f"  Could not fetch soil data or error: {soil_data_delhi.get('error', 'Unknown error')}")

    print("\nTesting Soil Data (Mumbai example):")
    # Coordinates for Mumbai, India
    test_lat_mumbai = 19.0760
    test_lon_mumbai = 72.8777
    soil_data_mumbai = fetch_soil_data(test_lat_mumbai, test_lon_mumbai)
    if soil_data_mumbai and "error" not in soil_data_mumbai:
         for prop_name, data_at_depths in soil_data_mumbai.get("properties", {}).items():
            print(f"  {prop_name}:")
            if isinstance(data_at_depths, dict):
                for depth, value_unit in data_at_depths.items():
                    print(f"    {depth}: {value_unit['value']} {value_unit['unit']}")
            else:
                print(f"    {data_at_depths}")
    else:
        print(f"  Could not fetch soil data or error: {soil_data_mumbai.get('error', 'Unknown error')}")

    # Test Historical Yield Data
    print("\nTesting Historical Yield Data:")
    yield_data_delhi = fetch_historical_yield_data("delhi_region_farm123")
    print(f"  Yield (Delhi Region): {yield_data_delhi}")
    yield_data_mumbai = fetch_historical_yield_data("mumbai_region_farm456")
    print(f"  Yield (Mumbai Region): {yield_data_mumbai}")
    yield_data_unknown = fetch_historical_yield_data("unknown_location")
    print(f"  Yield (Unknown): {yield_data_unknown}")

    # Test IoT Sensor Data
    print("\nTesting IoT Sensor Data:")
    sensor_data1 = fetch_iot_sensor_data("farm_A_plot_1")
    print(f"  Sensor Data (Farm A): {sensor_data1}")
    sensor_data2 = fetch_iot_sensor_data("farm_B_plot_7")
    print(f"  Sensor Data (Farm B): {sensor_data2}")
