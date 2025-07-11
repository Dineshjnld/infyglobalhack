# AgriGuru - Crop Suitability Model Module
# Trains and uses a machine learning model (e.g., Random Forest) to predict crop suitability.

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

from config import settings # To potentially define model paths

# Define a default path for the trained model
# MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'models') # Not robust if __file__ is not there
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'models'))
os.makedirs(MODEL_DIR, exist_ok=True) # Ensure directory exists
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, 'crop_suitability_random_forest.joblib')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'crop_suitability_preprocessor.joblib')


def preprocess_data_for_training(soil_data_list, yield_data_list, sensor_data_list, labels_list):
    """
    Preprocesses a list of data entries and corresponding labels for training.
    This is a simplified preprocessor. A real one would be more complex.

    Args:
        soil_data_list (list of dict): List of soil data dictionaries.
        yield_data_list (list of dict): List of historical yield data dictionaries.
        sensor_data_list (list of dict): List of IoT sensor data dictionaries.
        labels_list (list of str): List of crop name labels corresponding to each data entry.

    Returns:
        pd.DataFrame: Processed features.
        pd.Series: Labels.
        ColumnTransformer: Fitted preprocessor object.
    """
    records = []
    for i in range(len(labels_list)):
        soil = soil_data_list[i].get('properties', {}) if soil_data_list[i] and isinstance(soil_data_list[i], dict) else {}
        # For simplicity, average top layer soil data or take a specific one if available
        # Example: pH from '0-5cm' or average if multiple depths
        def get_soil_value(prop_name, depth_label='0-5cm'):
            prop = soil.get(prop_name, {})
            if isinstance(prop, dict) and depth_label in prop:
                return prop[depth_label].get('value')
            return np.nan # Return NaN if not found

        record = {
            'ph': get_soil_value('pH water'),
            'soc_percent': get_soil_value('Soil Organic Carbon'), # Assuming it's already %
            'clay_percent': get_soil_value('Clay Content'),
            'sand_percent': get_soil_value('Sand Content'),
            'silt_percent': get_soil_value('Silt Content'),
            'cec': get_soil_value('Cation Exchange Capacity'),
            'bdod': get_soil_value('Bulk Density'),
            # Simplified yield - using a dummy 'dominant_crop_yield' for now
            'dominant_crop_avg_yield': yield_data_list[i].get(list(yield_data_list[i].keys())[0], {}).get('avg_yield_kg_ha', 0) if yield_data_list[i] and isinstance(yield_data_list[i], dict) and yield_data_list[i] else 0,
            'soil_moisture_percent': sensor_data_list[i].get('soil_moisture_percent', np.nan) if sensor_data_list[i] and isinstance(sensor_data_list[i], dict) else np.nan,
            'air_temp_celsius': sensor_data_list[i].get('air_temperature_celsius', np.nan) if sensor_data_list[i] and isinstance(sensor_data_list[i], dict) else np.nan,
            # Add other relevant features: e.g., location type (categorical, needs OHE)
            # For now, keeping it simple with numerical features.
        }
        records.append(record)

    df = pd.DataFrame(records)
    df = df.fillna(df.median()) # Simple imputation for missing values

    X = df
    y = pd.Series(labels_list)

    # Define preprocessing steps (only scaling for now as all are numeric)
    # In a real scenario, you'd have categorical features too (e.g., soil type text, region)
    # which would require OneHotEncoder or similar.
    numerical_features = X.columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features)
        ],
        remainder='passthrough' # In case some columns are not in numerical_features
    )

    X_processed = preprocessor.fit_transform(X)

    # Save the fitted preprocessor
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Preprocessor saved to {PREPROCESSOR_PATH}")

    return X_processed, y, preprocessor


def train_crop_suitability_model(features, labels, model_path=DEFAULT_MODEL_PATH):
    """
    Trains a Random Forest classifier for crop suitability.
    Saves the trained model to disk.
    """
    if features is None or labels is None or not len(features) or not len(labels):
        print("ERROR: Features or labels are empty. Cannot train model.")
        return None

    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42, stratify=labels if len(np.unique(labels)) > 1 else None)

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced') # Added class_weight

    try:
        model.fit(X_train, y_train)
    except ValueError as e:
        print(f"ERROR training model: {e}. This might be due to insufficient samples for some classes after split.")
        # This often happens if a class has only 1 sample and stratify is attempted.
        # Or if X_train is empty for some reason.
        print(f"X_train shape: {X_train.shape}, y_train unique counts: {np.unique(y_train, return_counts=True)}")
        return None

    y_pred = model.predict(X_test)

    print(f"\nModel Training Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    if len(np.unique(y_test)) > 1 : # Classification report needs multiple classes
         print("Classification Report:")
         print(classification_report(y_test, y_pred, zero_division=0))
    else:
        print("Classification report skipped as there is only one class in y_test.")

    # Save the trained model
    joblib.dump(model, model_path)
    print(f"Trained model saved to {model_path}")
    return model

def load_model(model_path=DEFAULT_MODEL_PATH):
    """Loads a pre-trained model from disk."""
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"Model loaded from {model_path}")
        return model
    else:
        print(f"No pre-trained model found at {model_path}.")
        return None

def load_preprocessor(preprocessor_path=PREPROCESSOR_PATH):
    """Loads a pre-trained preprocessor from disk."""
    if os.path.exists(preprocessor_path):
        preprocessor = joblib.load(preprocessor_path)
        print(f"Preprocessor loaded from {preprocessor_path}")
        return preprocessor
    else:
        print(f"No preprocessor found at {preprocessor_path}.")
        return None

def predict_crop_suitability(model, preprocessor, input_data_dict_list):
    """
    Predicts crop suitability for new input data.
    input_data_dict_list: A list of dictionaries, where each dict is like the `record` in preprocess_data_for_training.
    """
    if model is None or preprocessor is None:
        return {"error": "Model or preprocessor not loaded."}

    df_input = pd.DataFrame(input_data_dict_list)
    # Ensure columns are in the same order as training and handle NaNs
    # This is simplified; ideally, use the preprocessor's known features.
    # df_input = df_input.fillna(df_input.median()) # Should use means/medians from training set
    # For now, we assume the preprocessor handles NaNs via its pipeline (e.g. SimpleImputer if added)
    # The current StandardScaler does not handle NaNs, so NaNs must be imputed before scaling.

    # Temporary imputation to match training preprocessing step
    # In a robust pipeline, an imputer would be part of the saved preprocessor.
    df_input_filled = df_input.fillna(0) # Simplistic fillna for prediction. Should use training data imputation values.


    try:
        input_features_processed = preprocessor.transform(df_input_filled)
    except Exception as e:
        return {"error": f"Error during preprocessing input data: {e}. Ensure input data structure matches training."}

    predictions = model.predict(input_features_processed)
    probabilities = model.predict_proba(input_features_processed)

    results = []
    for i, pred_crop in enumerate(predictions):
        probs_for_sample = probabilities[i]
        # Get class order from the model
        class_labels = model.classes_
        suitability_scores = {crop: f"{prob*100:.2f}%" for crop, prob in zip(class_labels, probs_for_sample)}
        results.append({
            "predicted_crop": pred_crop,
            "suitability_scores": suitability_scores # Probabilities for all learned crops
        })
    return results


# --- Dummy Data Generation and Example Usage ---
def generate_dummy_training_data(num_samples=200):
    """Generates dummy data for training the crop suitability model."""
    # Simulate fetched data structure
    dummy_soil_data = []
    for _ in range(num_samples):
        soil_props = {
            'pH water': {'0-5cm': {'value': np.random.uniform(5.0, 8.5)}},
            'Soil Organic Carbon': {'0-5cm': {'value': np.random.uniform(0.5, 5.0)}}, # Assuming %
            'Clay Content': {'0-5cm': {'value': np.random.uniform(10.0, 60.0)}}, # Assuming %
            'Sand Content': {'0-5cm': {'value': np.random.uniform(10.0, 60.0)}}, # Assuming %
            'Silt Content': {'0-5cm': {'value': np.random.uniform(10.0, 60.0)}}, # Assuming %
            'Cation Exchange Capacity': {'0-5cm': {'value': np.random.uniform(5.0, 25.0)}},
            'Bulk Density': {'0-5cm': {'value': np.random.uniform(1.0, 1.8)}}
        }
        # Ensure texture sum is somewhat reasonable (though independent random might not be perfect)
        total_texture = soil_props['Clay Content']['0-5cm']['value'] + \
                        soil_props['Sand Content']['0-5cm']['value'] + \
                        soil_props['Silt Content']['0-5cm']['value']
        if total_texture > 0 : # Avoid division by zero
            soil_props['Clay Content']['0-5cm']['value'] = (soil_props['Clay Content']['0-5cm']['value'] / total_texture) * 100
            soil_props['Sand Content']['0-5cm']['value'] = (soil_props['Sand Content']['0-5cm']['value'] / total_texture) * 100
            soil_props['Silt Content']['0-5cm']['value'] = (soil_props['Silt Content']['0-5cm']['value'] / total_texture) * 100
        dummy_soil_data.append({'properties': soil_props})

    dummy_yield_data = [{'wheat': {'avg_yield_kg_ha': np.random.randint(2000, 5000)}} for _ in range(num_samples)]
    dummy_sensor_data = [{
        'soil_moisture_percent': np.random.uniform(15, 75),
        'air_temperature_celsius': np.random.uniform(10, 45)
    } for _ in range(num_samples)]

    # Generate labels (crop names)
    possible_crops = ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane"]
    # Ensure enough samples for each class for stratification
    min_samples_per_class = 2
    if num_samples < len(possible_crops) * min_samples_per_class:
        # If not enough samples overall, just repeat the first crop or use fewer crops
        print(f"Warning: num_samples ({num_samples}) is too small for diverse classes. Adjusting label generation.")
        dummy_labels = np.random.choice(possible_crops[:max(1, num_samples // min_samples_per_class)], num_samples).tolist()
    else:
        # Try to distribute classes somewhat, then fill randomly
        base_labels = []
        for crop in possible_crops:
            base_labels.extend([crop] * min_samples_per_class)
        remaining_samples = num_samples - len(base_labels)
        if remaining_samples > 0:
            base_labels.extend(np.random.choice(possible_crops, remaining_samples).tolist())
        dummy_labels = np.random.permutation(base_labels).tolist()


    return dummy_soil_data, dummy_yield_data, dummy_sensor_data, dummy_labels


if __name__ == '__main__':
    print("--- Testing Crop Suitability Model ---")

    # 1. Generate Dummy Data
    print("\n1. Generating dummy data...")
    num_train_samples = 50 # Reduced for faster testing, ensure > (num_classes * 2)
    s_data, y_data, sen_data, labels = generate_dummy_training_data(num_samples=num_train_samples)
    print(f"Generated {len(labels)} samples.")
    # print(f"Sample soil: {s_data[0]}")
    # print(f"Sample yield: {y_data[0]}")
    # print(f"Sample sensor: {sen_data[0]}")
    # print(f"Sample label: {labels[0]}")


    # 2. Preprocess Data
    print("\n2. Preprocessing data...")
    # Wrap single sample data in lists if that's what preprocess_data_for_training expects
    features_processed, labels_series, preprocessor_fitted = preprocess_data_for_training(s_data, y_data, sen_data, labels)
    if features_processed is not None:
        print(f"Processed features shape: {features_processed.shape}")
        print(f"Labels shape: {labels_series.shape}")

        # 3. Train Model
        print("\n3. Training model...")
        trained_model = train_crop_suitability_model(features_processed, labels_series)

        if trained_model:
            # 4. Load Model & Preprocessor (Simulating a new run)
            print("\n4. Loading model and preprocessor...")
            loaded_model = load_model()
            loaded_preprocessor = load_preprocessor()

            if loaded_model and loaded_preprocessor:
                # 5. Predict on New Dummy Data
                print("\n5. Predicting on new dummy data...")
                # Generate a few new samples for prediction
                s_new, y_new, sen_new, _ = generate_dummy_training_data(num_samples=5)

                # Construct input_data_dict_list for prediction
                # This needs to match the structure expected by the preprocessor (raw dicts before transformation)
                prediction_input_dicts = []
                for i in range(len(s_new)):
                    soil = s_new[i].get('properties', {}) if s_new[i] and isinstance(s_new[i], dict) else {}
                    def get_soil_val(prop_name, depth_label='0-5cm'):
                        prop = soil.get(prop_name, {})
                        if isinstance(prop, dict) and depth_label in prop: return prop[depth_label].get('value')
                        return np.nan

                    record = {
                        'ph': get_soil_val('pH water'),
                        'soc_percent': get_soil_val('Soil Organic Carbon'),
                        'clay_percent': get_soil_val('Clay Content'),
                        'sand_percent': get_soil_val('Sand Content'),
                        'silt_percent': get_soil_val('Silt Content'),
                        'cec': get_soil_val('Cation Exchange Capacity'),
                        'bdod': get_soil_val('Bulk Density'),
                        'dominant_crop_avg_yield': y_new[i].get(list(y_new[i].keys())[0], {}).get('avg_yield_kg_ha', 0) if y_new[i] and isinstance(y_new[i], dict) and y_new[i] else 0,
                        'soil_moisture_percent': sen_new[i].get('soil_moisture_percent', np.nan) if sen_new[i] and isinstance(sen_new[i], dict) else np.nan,
                        'air_temp_celsius': sen_new[i].get('air_temperature_celsius', np.nan) if sen_new[i] and isinstance(sen_new[i], dict) else np.nan,
                    }
                    prediction_input_dicts.append(record)

                predictions = predict_crop_suitability(loaded_model, loaded_preprocessor, prediction_input_dicts)
                print("Predictions:")
                import json
                print(json.dumps(predictions, indent=2))
            else:
                print("Could not load model or preprocessor for prediction test.")
        else:
            print("Model training failed. Skipping prediction test.")
    else:
        print("Data preprocessing failed. Skipping model training and prediction.")

    print("\n--- Crop Suitability Model Test Complete ---")
