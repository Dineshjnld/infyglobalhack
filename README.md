# AgriGuru: Intelligent Agricultural Advisory System 🌾

AgriGuru is now a conversational AI chatbot designed to provide intelligent agricultural advice. Users can ask questions in natural language, and AgriGuru will use its knowledge along with real-time or near real-time data from various APIs to provide comprehensive answers.

## Key Features

*   **Conversational Interface:** Interact with AgriGuru through a chat interface.
*   **Location-Specific Advice:** Set your village/location to get tailored advice. AgriGuru uses this for:
    *   **Weather Conditions:** Fetches current weather using the Open-Meteo API.
    *   **Soil Data:** Retrieves estimated soil properties (pH, organic carbon, texture, etc.) for your location from ISRIC SoilGrids.
    *   **Personalized Recommendations:** OpenAI (GPT-3.5 Turbo) synthesizes information from these APIs along with your query to provide advice on crop selection, sustainable practices, and general agricultural questions.
*   **Market Insights (India Focus via AI):** For queries about market prices or trends in India, AgriGuru leverages OpenAI's general knowledge, contextualized by your set location. Direct integration of a live Indian market data API was challenging for this phase.
*   **USDA Market Data (Optional for US):** The underlying code for USDA NASS API access for US market data is still present but not actively used in the primary chat flow unless specifically triggered by very precise keywords (this explicit triggering is not fully fleshed out in the chat demo).

## How It Works

1.  **Set Your Location:** Use the sidebar to input your village/town and district. This is crucial for relevant advice.
2.  **Ask a Question:** Type your agricultural query into the chatbox.
3.  **Information Gathering (Orchestration):** Based on your query and location, AgriGuru's backend may:
    *   Fetch current weather from Open-Meteo.
    *   Fetch estimated soil data from ISRIC SoilGrids.
4.  **AI Synthesis:** The collected data (if any) along with your query and location are sent to OpenAI (GPT-3.5 Turbo).
5.  **Response:** AgriGuru provides an answer synthesized by OpenAI, incorporating the fetched data and its general agricultural knowledge. If specific live data (like hyper-local market prices) isn't available from APIs, the AI will use its broader knowledge for your region.

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
    *   **`OPENAI_API_KEY`**: Obtain this from [OpenAI Platform](https://platform.openai.com/api-keys). This is essential for the AI's conversational abilities and for synthesizing information. The application uses the GPT-3.5 Turbo model.
    *   **`USDA_API_KEY`**: Obtain this from the [USDA NASS QuickStats API website](https://quickstats.nass.usda.gov/api) (it's free). This is currently optional and primarily for US-specific market data if explicitly queried in a way the (not fully implemented) USDA trigger understands.

    If the `OPENAI_API_KEY` is not provided or is invalid, the chatbot will not be able to provide AI-generated responses and will show an error or limited mocked replies.
    The Open-Meteo (weather) and ISRIC SoilGrids (soil) APIs used in this prototype do not require API keys for basic access.

    *   **Streamlit Secrets (Alternative for deployed apps)**:
        If deploying to Streamlit Community Cloud, you can set API keys as secrets in your app's settings instead of using a `.env` file. The environment variable names (`OPENAI_API_KEY`, `USDA_API_KEY`) remain the same.

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Ensure you have created and populated the `.env` file with your `OPENAI_API_KEY` (and `USDA_API_KEY` if you intend to query US data specifically).
3.  Run the Streamlit app from your terminal:
    ```bash
    streamlit run app.py
    ```
4.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

## Using the App

1.  **Set Your Location:** Use the sidebar input field to "Enter your Village/Town, District:" and click "Set Location". This context is used for all subsequent queries. If not set, the bot will remind you.
2.  **Chat with AgriGuru:** Type your agricultural questions into the chat input at the bottom of the screen. Examples:
    *   "What's the weather forecast for today?"
    *   "What are the typical soil properties here?"
    *   "What crops are suitable for my location given this weather and soil?"
    *   "Tell me about sustainable farming practices for [crop name]."
    *   "What are the general market trends for rice in India?"

**Note:** The quality and specificity of AI responses depend on the clarity of your questions, the set location, and the data retrieved from the integrated APIs (Open-Meteo for weather, ISRIC SoilGrids for estimated soil properties). For Indian market data, the bot currently uses OpenAI's general knowledge based on your location.

## Future Development Ideas

*   **Integrate Direct Indian Market Data APIs:** If suitable free and accessible APIs are found (e.g., for live Mandi prices).
*   **More Sophisticated Intent Recognition:** Move beyond simple keyword spotting to a more robust Natural Language Understanding (NLU) component or leverage OpenAI's function calling for tool use.
*   **User Accounts & History:** Save conversation history and location preferences for users.
*   **Expanded Knowledge Base/APIs:** Integrate more specialized agricultural APIs (e.g., pest/disease databases, advanced satellite imagery).
*   **Proactive Alerts:** (Future) Notifications for weather events or market changes.
*   **Multi-language Support.**
