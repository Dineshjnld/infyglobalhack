# AgriGuru: AI-Powered Agricultural Advisory Platform

AgriGuru is an AI-powered platform designed to provide smallholder farmers in India with personalized crop recommendations, real-time weather forecasts, market price insights, crop health monitoring, and precision irrigation advice. This project aims to leverage satellite data, local IoT sensors (simulated initially), open-source AI models, and free APIs to deliver localized, actionable insights.

**Project Goal:** To address the lack of real-time, localized agricultural information by building a scalable, offline-capable platform using open-source technologies, optimized for systems with 16 GB RAM and a 4 GB GPU.

**Current Development Phase:** Implementation of Core Modules based on the detailed Requirement Report. This README will be updated as more modules are completed.

**Currently Implemented (Partially or Fully):**
*   **Personalized Crop Recommendations Module:**
    *   Fetches soil data (SoilGrids via REST API, with `soilDB` as an option).
    *   Simulates fetching historical yield and IoT sensor data.
    *   Trains a Scikit-learn (Random Forest) model for crop suitability based on this data.
    *   Uses a Hugging Face Transformer model (FLAN-T5 Small) to generate textual planting advice for recommended crops.
    *   Provides an orchestrated output in JSON format.

## Project Structure

The project follows the structure outlined in the Requirement Report:
```
agriguru/
├── main.py                 # Main application entry point (e.g., for Rasa/Flask/FastAPI - currently placeholder)
├── requirements.txt        # Python dependencies
├── config.py               # Configuration and API keys management
├── .env.example            # Example environment variable file
├── modules/                # Core logic modules
│   ├── __init__.py
│   ├── crop_data_fetcher.py    # Fetches data for crop recommendations
│   ├── crop_suitability_model.py # ML model for crop suitability
│   ├── crop_nlp_generator.py   # NLP for generating textual advice
│   ├── recommendation_engine.py # Orchestrates crop recommendations
│   └── ...                 # Other modules (weather, market, satellite, etc. - TBD)
├── data/                   # Data storage (models, cache, profiles, knowledge base)
│   ├── models/             # Saved ML models, HF cache
│   ├── cached_data/        # Offline data storage (SQLite DB planned)
│   ├── farmer_profiles/    # (TBD)
│   └── knowledge_base/     # (TBD)
├── assets/                 # UI assets (images, translations, icons)
├── tests/                  # Unit and integration tests
└── docs/                   # Project documentation
```

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    # git clone <repository_url> # If this were a git repo
    # cd agriguru
    ```
    Ensure you have all the files in the `agriguru` directory.

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install all required Python packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *Note on `soilDB` and `GDAL`*: The `soilDB` library can have complex dependencies, particularly GDAL. If you encounter issues installing `soilDB` or its dependencies, the `crop_data_fetcher.py` module currently uses a direct REST API call to SoilGrids as a primary method for fetching soil data, so `soilDB` is not strictly critical for the current crop recommendation functionality if its installation is problematic.

4.  **Set Up Environment Variables:**
    API keys and sensitive configurations are managed via an `.env` file.
    *   Copy the example file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your actual API keys and configurations. Refer to `config.py` and `.env.example` for the list of expected variables.
        *   **`OPENAI_API_KEY`**: Required if any module directly uses OpenAI (the current NLP generator uses Hugging Face models by default, but OpenAI GPT-4 is mentioned in the broader brief for the main ConversationalAI).
        *   **`SENTINEL_API_CLIENT_ID` / `SENTINEL_API_CLIENT_SECRET`**: If using Sentinel Hub for satellite imagery.
        *   **`OPENWEATHERMAP_API_KEY`**: For OpenWeatherMap.
        *   **`NASA_POWER_API_KEY`**: For NASA POWER (often not needed for basic access).
        *   **`GOOGLE_TRANSLATE_API_KEY`**: For Google Translate.
        *   Other keys as per `.env.example` for future modules.

5.  **Download Hugging Face Models (First Run):**
    The first time you run a module that uses Hugging Face Transformers (like `crop_nlp_generator.py`), it will download the specified pre-trained model files. These will be cached locally (by default in `~/.cache/huggingface/transformers/` or in `agriguru/data/models/hf_cache/` as configured in `crop_nlp_generator.py`). This might take some time and requires an internet connection.

## Running Modules (Example: Crop Recommendation)

Currently, the project is being built module by module. You can test individual modules if they have a `if __name__ == '__main__':` block.

**To test the Personalized Crop Recommendation flow:**

1.  **Train the ML Model (if not already done):**
    The `crop_suitability_model.py` script can generate dummy data and train a model. This saved model (`crop_suitability_random_forest.joblib` and `crop_suitability_preprocessor.joblib` in `data/models/`) is needed by the recommendation engine.
    ```bash
    python modules/crop_suitability_model.py
    ```
    This will also download the Hugging Face model used by `crop_nlp_generator.py` if you run its main block, or it will be downloaded when `recommendation_engine.py` calls it.

2.  **Run the Recommendation Engine Test:**
    The `recommendation_engine.py` has a test script in its `if __name__ == '__main__':` block.
    ```bash
    python modules/recommendation_engine.py
    ```
    This will output a JSON string with crop recommendations for a sample location.

## Future Development

This project will be developed iteratively, adding modules for:
*   Real-Time Weather Forecasts (NASA POWER, GSODR, PyETo, XGBoost/LSTM)
*   Market Price Insights (Agmarknet scraping, Prophet, LLaMA/Falcon)
*   Crop Health Monitoring (Sentinel-2, PlantVillage, YOLOv8n/ViT, OpenCV)
*   Precision Irrigation (SMAP, IoT, Random Forest/LSTM, PyTSEB)
*   Farmer-Friendly Interface (Rasa chatbot, Flask/FastAPI dashboard)
*   Edge Computing & Offline Functionality (Open Horizon, MQTT, SQLite)
*   Community Knowledge Sharing (OpenFarm, Growstuff, Discourse)

Refer to the full Requirement Report for detailed specifications of each module.

## Contributing
(Details TBD)

## License
(Details TBD)
