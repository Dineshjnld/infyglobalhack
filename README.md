# AgriGuru: Intelligent Agricultural Advisory System 🌾

AgriGuru is a prototype Streamlit application designed to provide intelligent agricultural advice to farmers. It aims to offer personalized crop recommendations, weather forecasts, market insights, and information on sustainable farming practices, leveraging AI capabilities (now powered by OpenAI).

## Features

*   **Crop Recommendations:** Get suggestions for crops based on location, soil type, and other environmental factors (uses OpenAI API - GPT-3.5 Turbo).
*   **Weather Forecast:** Access real-time weather forecasts for your region using the Open-Meteo API. Automatically geocodes location names.
*   **Market Insights:** Obtain US agricultural market price information from the USDA NASS API. Falls back to OpenAI (GPT-3.5 Turbo) for general insights if the USDA key is unavailable.
*   **Sustainable Farming Practices:** Ask questions and get advice on sustainable agriculture (uses OpenAI API - GPT-3.5 Turbo).

## Setup and Installation

1.  **Clone the repository (or ensure all files are in one directory):**
    Make sure you have `app.py`, `requirements.txt`, and `.env.example` in your project directory.

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Keys:**
    The application uses a `.env` file to manage API keys.
    1.  Rename the provided `.env.example` file in the root directory to `.env`.
    2.  Open the `.env` file and add your API keys:

        ```env
        OPENAI_API_KEY="YOUR_ACTUAL_OPENAI_API_KEY"
        USDA_API_KEY="YOUR_ACTUAL_USDA_NASS_API_KEY"
        ```
    *   **`OPENAI_API_KEY`**: Obtain this from [OpenAI Platform](https://platform.openai.com/api-keys). This is used for crop recommendations, sustainable farming advice, and as a fallback for market insights if the USDA key is not provided. The application primarily uses the GPT-3.5 Turbo model.
    *   **`USDA_API_KEY`**: Obtain this from the [USDA NASS QuickStats API website](https://quickstats.nass.usda.gov/api) (it's free). This is used for the "Market Insights" section to fetch agricultural price data (primarily US-focused).

    If the `OPENAI_API_KEY` is not provided or is invalid, the AI-powered features will use mocked responses or show an error.
    If the `USDA_API_KEY` is not provided, the "Market Insights" section will attempt to use OpenAI (GPT-3.5 Turbo) for general insights or show a warning.

    *   **Streamlit Secrets (Alternative for deployed apps)**:
        If deploying to Streamlit Community Cloud, you can set these as secrets in your app's settings instead of using a `.env` file. The environment variable names (`OPENAI_API_KEY`, `USDA_API_KEY`) remain the same.

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Ensure you have created and populated the `.env` file with your API keys (or set them as environment variables/secrets).
3.  Run the Streamlit app from your terminal:
    ```bash
    streamlit run app.py
    ```
4.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

## Using the App

*   **Crop Recommendations:** Provide location, soil type, average rainfall, and temperature to get crop suggestions from OpenAI.
*   **Weather Forecast:** Enter a city or region name. The app uses the Open-Meteo API to fetch current weather and a 7-day forecast. It automatically converts the location name to latitude/longitude. No separate API key is needed for this feature as implemented.
*   **Market Insights:** Select or enter a commodity name (e.g., "CORN", "SOYBEANS"), year, and optionally a US state to get price data from the USDA NASS API. If the USDA API key is not configured, it may fall back to OpenAI for general insights.
*   **Sustainable Farming Practices:** Ask questions in the text area to get advice on sustainable agriculture from OpenAI.

**Note:** Functionality requiring API keys will be limited or use mocked/fallback data if keys are missing or invalid. Check the application's warnings if you encounter issues. The AI responses are powered by OpenAI's GPT-3.5 Turbo model.

## Future Development Ideas

*   Integrate real satellite imagery APIs for more precise local data.
*   Connect to live agricultural sensor data streams.
*   More sophisticated data input for crop recommendations (e.g., historical yield data).
*   User accounts and personalized dashboards.
*   Broader international market data sources (if suitable free APIs are found).
*   More detailed weather information (e.g., hourly forecasts, soil temperature).
