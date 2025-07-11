# AgriGuru - Recommendation Engine Module
# Orchestrates the process of generating personalized crop recommendations.

import json
import numpy as np
import pandas as pd

# Import module functions - assuming they are in the same package 'modules'
from .crop_data_fetcher import fetch_soil_data, fetch_historical_yield_data, fetch_iot_sensor_data
from .crop_suitability_model import load_model as load_suitability_model, \
                                     load_preprocessor as load_suitability_preprocessor, \
                                     predict_crop_suitability, DEFAULT_MODEL_PATH, PREPROCESSOR_PATH
from .crop_nlp_generator import generate_planting_advice, load_nlp_model_and_tokenizer

# Global cache for models and preprocessor to avoid reloading on every call within the same session/run
# This is a simple in-memory cache. For a multi-user or long-running app, more robust caching might be needed.
_suitability_model_cache = None
_suitability_preprocessor_cache = None
_nlp_pipeline_cache = None


def _get_suitability_model_and_preprocessor():
    """Loads (or retrieves from cache) the suitability model and preprocessor."""
    global _suitability_model_cache, _suitability_preprocessor_cache
    if _suitability_model_cache is None:
        _suitability_model_cache = load_suitability_model(DEFAULT_MODEL_PATH)
    if _suitability_preprocessor_cache is None:
        _suitability_preprocessor_cache = load_suitability_preprocessor(PREPROCESSOR_PATH)
    return _suitability_model_cache, _suitability_preprocessor_cache

def _get_nlp_pipeline():
    """Loads (or retrieves from cache) the NLP pipeline."""
    global _nlp_pipeline_cache
    if _nlp_pipeline_cache is None:
        _nlp_pipeline_cache = load_nlp_model_and_tokenizer() # Uses default model from nlp_generator
    return _nlp_pipeline_cache


def get_crop_recommendations(latitude, longitude, location_identifier="default_location", farm_id="default_farm", top_n_crops=3):
    """
    Main orchestration function to get personalized crop recommendations.

    Args:
        latitude (float): Latitude of the farm/location.
        longitude (float): Longitude of the farm/location.
        location_identifier (str): Identifier for fetching historical yield data (e.g., region, district).
        farm_id (str): Identifier for fetching IoT sensor data.
        top_n_crops (int): Number of top crop recommendations to provide detailed advice for.

    Returns:
        str: JSON string containing ranked crop recommendations with suitability scores and planting advice.
             Returns JSON string with an error message if critical components fail.
    """
    print(f"INFO: [RecommendationEngine] Starting crop recommendation for lat={latitude}, lon={longitude}")

    # 1. Fetch Data
    print("INFO: [RecommendationEngine] Fetching data...")
    soil_data = fetch_soil_data(latitude, longitude)
    # The brief implies historical yield might be linked to location_identifier rather than specific lat/lon for FAO data.
    historical_yield_data = fetch_historical_yield_data(location_identifier)
    iot_sensor_data = fetch_iot_sensor_data(farm_id)

    # Basic check for critical data
    if not soil_data or "error" in soil_data:
        print(f"ERROR: [RecommendationEngine] Failed to fetch critical soil data: {soil_data}")
        return json.dumps({"error": "Failed to fetch critical soil data.", "details": soil_data})

    # 2. Prepare Input for ML Model Prediction
    # The predict_crop_suitability function expects a list of dictionaries.
    # We need to transform the fetched data into this format.
    # This structure should mirror what preprocess_data_for_training created the features from.

    # Helper to safely extract soil property values for a specific depth, returning np.nan if not found
    def get_soil_feature_value(prop_name, depth_label='0-5cm'):
        s_props = soil_data.get('properties', {})
        prop_info = s_props.get(prop_name, {})
        if isinstance(prop_info, dict) and depth_label in prop_info:
            return prop_info[depth_label].get('value')
        return np.nan

    # Construct the single input record for prediction
    # This must match the feature order and names used during preprocessor fitting.
    # The preprocessor was fitted on: ['ph', 'soc_percent', 'clay_percent', 'sand_percent', 'silt_percent', 'cec', 'bdod', 'dominant_crop_avg_yield', 'soil_moisture_percent', 'air_temp_celsius']
    # Ensure units are consistent with training if direct values are used (e.g. % for SOC, clay etc.)
    # The current `get_soil_feature_value` returns the numerical value directly.

    # For 'dominant_crop_avg_yield', we need a strategy.
    # If multiple crops in yield_data, which one to use? For prediction, this might be less critical
    # or could be an average, or perhaps this feature is more for training.
    # For prediction, if we don't have a "current" dominant crop, we might use a default or average.
    # For now, using the first available yield or 0.
    first_yield_key = list(historical_yield_data.keys())[0] if historical_yield_data and isinstance(historical_yield_data, dict) and historical_yield_data else None
    dominant_yield = historical_yield_data.get(first_yield_key, {}).get('avg_yield_kg_ha', 0) if first_yield_key else 0
    if isinstance(dominant_yield, dict) : dominant_yield = 0 # Handle cases where it might be a message

    input_record = {
        'ph': get_soil_feature_value('pH water'),
        'soc_percent': get_soil_feature_value('Soil Organic Carbon'),
        'clay_percent': get_soil_feature_value('Clay Content'),
        'sand_percent': get_soil_feature_value('Sand Content'),
        'silt_percent': get_soil_feature_value('Silt Content'),
        'cec': get_soil_feature_value('Cation Exchange Capacity'),
        'bdod': get_soil_feature_value('Bulk Density'),
        'dominant_crop_avg_yield': dominant_yield,
        'soil_moisture_percent': iot_sensor_data.get('soil_moisture_percent', np.nan) if iot_sensor_data else np.nan,
        'air_temp_celsius': iot_sensor_data.get('air_temperature_celsius', np.nan) if iot_sensor_data else np.nan,
    }
    prediction_input_list = [input_record]
    # print(f"DEBUG: [RecommendationEngine] Input record for ML prediction: {prediction_input_list}")

    # 3. Load ML Model and Preprocessor
    print("INFO: [RecommendationEngine] Loading suitability model and preprocessor...")
    suitability_model, suitability_preprocessor = _get_suitability_model_and_preprocessor()

    if not suitability_model or not suitability_preprocessor:
        msg = "ERROR: [RecommendationEngine] Crop suitability model or preprocessor not available. Train the model first."
        print(msg)
        return json.dumps({"error": msg})

    # 4. Make Suitability Predictions
    print("INFO: [RecommendationEngine] Predicting crop suitability...")
    # predict_crop_suitability expects a list of dicts
    ml_predictions_result = predict_crop_suitability(suitability_model, suitability_preprocessor, prediction_input_list)

    if not ml_predictions_result or "error" in ml_predictions_result:
        msg = f"ERROR: [RecommendationEngine] Failed to get ML predictions: {ml_predictions_result}"
        print(msg)
        return json.dumps({"error": "Failed to get ML predictions.", "details": ml_predictions_result})

    # Assuming ml_predictions_result is a list (even if for one input sample)
    # Example: [{'predicted_crop': 'Wheat', 'suitability_scores': {'Wheat': '90.50%', 'Rice': '8.00%'}}]
    # We need to rank all crops based on suitability_scores for the first (and only) prediction input
    first_prediction_details = ml_predictions_result[0]
    all_crop_scores = first_prediction_details.get('suitability_scores', {})

    # Convert string percentages to float for sorting
    ranked_scores = []
    for crop, score_str in all_crop_scores.items():
        try:
            score_float = float(score_str.replace('%', ''))
            ranked_scores.append({'crop': crop, 'suitability_score_percent': score_float})
        except ValueError:
            print(f"WARN: [RecommendationEngine] Could not parse score for {crop}: {score_str}")
            ranked_scores.append({'crop': crop, 'suitability_score_percent': 0.0}) # Default to 0 if parsing fails

    # Sort by suitability score in descending order
    ranked_scores.sort(key=lambda x: x['suitability_score_percent'], reverse=True)

    top_predictions_for_nlp = []
    for item in ranked_scores[:top_n_crops]:
        top_predictions_for_nlp.append({
            "predicted_crop": item['crop'],
            "suitability_scores": {item['crop']: f"{item['suitability_score_percent']:.2f}%"} # Reconstruct for NLP input
        })

    # print(f"DEBUG: [RecommendationEngine] Top {top_n_crops} predictions for NLP: {top_predictions_for_nlp}")

    # 5. Generate NLP Planting Advice for Top N Crops
    print("INFO: [RecommendationEngine] Generating NLP planting advice...")
    _ = _get_nlp_pipeline() # Ensure NLP model is loaded (or cached)

    # generate_planting_advice expects a list of dicts, each with 'predicted_crop' and 'suitability_scores'
    # The 'suitability_scores' within this list for NLP should ideally be just for that crop.
    # Let's reformat based on what generate_planting_advice expects from its docstring.
    # Its docstring says: [{'predicted_crop': 'Wheat', 'suitability_scores': {'Wheat': '90.50%', 'Rice': '8.00%'}}]
    # But it actually uses only the score of the 'predicted_crop'. So, our `top_predictions_for_nlp` is fine.

    nlp_advices = generate_planting_advice(top_predictions_for_nlp)
    # nlp_advices is like: [{'crop': 'Wheat', 'suitability': '90.50%', 'advice': '...'}, ...]

    # 6. Format Final Output
    # Combine ML rankings with NLP advice
    final_recommendations = []
    for ranked_item in ranked_scores: # Iterate through all ranked crops
        crop_name = ranked_item['crop']
        suitability_str = f"{ranked_item['suitability_score_percent']:.2f}%"

        # Find NLP advice if this crop was in top_n
        advice_for_crop = "General advice: Follow local best practices. (Detailed NLP advice for top crops only)"
        for nlp_item in nlp_advices:
            if nlp_item['crop'] == crop_name:
                advice_for_crop = nlp_item['advice']
                break # Found advice for this crop

        final_recommendations.append({
            "crop": crop_name,
            "suitability": suitability_str,
            "planting_advice": advice_for_crop
        })

    output_json = {
        "location_input": {"latitude": latitude, "longitude": longitude, "identifier": location_identifier, "farm_id": farm_id},
        "retrieved_soil_summary": {prop: data.get('0-5cm', 'N/A') for prop, data in soil_data.get('properties', {}).items() if isinstance(data, dict)}, # Summary of top layer
        "retrieved_iot_summary": iot_sensor_data if iot_sensor_data else "Not available",
        "crop_recommendations": final_recommendations
    }

    print("INFO: [RecommendationEngine] Crop recommendation process complete.")
    return json.dumps(output_json, indent=2)


if __name__ == '__main__':
    print("--- Testing Recommendation Engine ---")

    # Ensure dependent models are trained/available by running their main blocks first if needed
    # (crop_suitability_model.py should be run to create the .joblib files)
    # (crop_nlp_generator.py should be run to download/cache HF model)

    # Test coordinates (New Delhi)
    test_lat = 28.6139
    test_lon = 77.2090
    test_loc_id = "delhi_urban_region"
    test_farm_id = "test_farm_001"

    print(f"\nRequesting recommendations for Lat: {test_lat}, Lon: {test_lon}")

    # First, ensure models are loaded into cache (or loaded for the first time)
    print("Pre-loading models (if not already cached by this session)...")
    _get_suitability_model_and_preprocessor()
    _get_nlp_pipeline()
    print("Models pre-loading attempt complete.")

    recommendations_json = get_crop_recommendations(test_lat, test_lon, test_loc_id, test_farm_id, top_n_crops=2)

    print("\n--- Final JSON Output ---")
    print(recommendations_json)

    # You would typically parse the JSON to display it or use it further
    # parsed_output = json.loads(recommendations_json)
    # print("\nParsed Top Recommended Crop:")
    # if "crop_recommendations" in parsed_output and parsed_output["crop_recommendations"]:
    #     print(f"  Crop: {parsed_output['crop_recommendations'][0]['crop']}")
    #     print(f"  Suitability: {parsed_output['crop_recommendations'][0]['suitability']}")
    #     print(f"  Advice: {parsed_output['crop_recommendations'][0]['planting_advice']}")
    # elif "error" in parsed_output:
    #      print(f"  Error: {parsed_output['error']}")


    print("\n--- Recommendation Engine Test Complete ---")
