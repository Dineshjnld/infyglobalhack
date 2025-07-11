# AgriGuru Configuration File
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# (User needs to set these in their .env file)

# For NLP and AI-driven insights (if any module still uses a general LLM beyond specified HF models)
# Or for services that might wrap HuggingFace models if direct use is too complex.
# The brief specifies "OpenAI GPT-4 API + Hugging Face transformers for offline mode".
# If GPT-4 is used directly, its key is needed.
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# For Satellite Data (as per brief Section 11.A) - Note: GEE usually uses OAuth2 not a simple key
# For direct GEE API calls, authentication is complex.
# If using a service that provides GEE data via a simpler API key, put it here.
# For now, Sentinel-2 access might be via a different API if not direct GEE.
# Sentinel Hub's sentinelhub-py library is a common way and uses OAuth client ID/secret.
SENTINEL_API_CLIENT_ID = os.getenv('SENTINEL_API_CLIENT_ID') # Example if using Sentinel Hub
SENTINEL_API_CLIENT_SECRET = os.getenv('SENTINEL_API_CLIENT_SECRET') # Example if using Sentinel Hub
# GOOGLE_EARTH_ENGINE_KEY = os.getenv('GOOGLE_EARTH_ENGINE_KEY') # As per brief, but GEE auth is usually not a single key.

# For Weather Data
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY') # Brief Section 11.A
NASA_POWER_API_KEY = os.getenv('NASA_POWER_API_KEY') # Brief Section 4 & 5 (NASA POWER is mentioned as free but sometimes requires a key for higher limits)

# For Language Translation (as per brief Section 11.A)
GOOGLE_TRANSLATE_API_KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY') # Requires Google Cloud Project

# Agmarknet / Growstuff - These might not have keys and rely on scraping or public endpoints
AGMARKNET_API_KEY = os.getenv('AGMARKNET_API_KEY') # If one exists
GROWSTUFF_API_KEY = os.getenv('GROWSTUFF_API_KEY') # If one exists

# Sencrop API for local weather stations (if available, as per brief)
SENCROP_API_KEY = os.getenv('SENCROP_API_KEY')

# --- Database Configuration ---
# For local caching (SQLite) and production (PostgreSQL)
# The brief specifies SQLite for local caching.
# DATABASE_URL will be used by SQLAlchemy or other ORMs if implemented.
# For SQLite, it can be like: 'sqlite:///./data/agriguru_cache.db'
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///./data/agriguru_cache.db")
# For PostgreSQL (example):
# DATABASE_URL_PROD = os.getenv('DATABASE_URL_PROD', 'postgresql://user:password@host:port/database')


# --- Cache Settings ---
CACHE_EXPIRY_HOURS = int(os.getenv('CACHE_EXPIRY_HOURS', "24"))
OFFLINE_MODE_ENABLED = os.getenv('OFFLINE_MODE_ENABLED', 'True').lower() == 'true'

# --- Model Paths & Settings ---
# Example:
# CROP_SUITABILITY_MODEL_PATH = os.getenv('CROP_SUITABILITY_MODEL_PATH', './data/models/crop_suitability_random_forest.joblib')
# YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', './data/models/yolov8n_pest_detection.pt')

# --- MQTT Broker Settings (for IoT & Edge Computing) ---
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
# MQTT_TLS_CERTFILE = os.getenv('MQTT_TLS_CERTFILE') # For secure connection

# --- Other Settings ---
# Example: Default location if not set by user (though user-set location is primary)
# DEFAULT_LATITUDE = float(os.getenv('DEFAULT_LATITUDE', '20.5937')) # India's approx center
# DEFAULT_LONGITUDE = float(os.getenv('DEFAULT_LONGITUDE', '78.9629'))

# Logging Configuration (basic example)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

print(f"Config loaded. DB URL (example): {DATABASE_URL}")
# Avoid printing sensitive keys here in a real app's startup log unless for specific debug and not in production.
# print(f"OpenAI Key Loaded: {'Yes' if OPENAI_API_KEY else 'No'}")

class Settings:
    """Class to hold all settings, making them easily accessible."""
    OPENAI_API_KEY: str = OPENAI_API_KEY
    SENTINEL_API_CLIENT_ID: str = SENTINEL_API_CLIENT_ID
    SENTINEL_API_CLIENT_SECRET: str = SENTINEL_API_CLIENT_SECRET
    OPENWEATHERMAP_API_KEY: str = OPENWEATHERMAP_API_KEY
    NASA_POWER_API_KEY: str = NASA_POWER_API_KEY
    GOOGLE_TRANSLATE_API_KEY: str = GOOGLE_TRANSLATE_API_KEY
    AGMARKNET_API_KEY: str = AGMARKNET_API_KEY
    GROWSTUFF_API_KEY: str = GROWSTUFF_API_KEY
    SENCROP_API_KEY: str = SENCROP_API_KEY

    DATABASE_URL: str = DATABASE_URL
    CACHE_EXPIRY_HOURS: int = CACHE_EXPIRY_HOURS
    OFFLINE_MODE_ENABLED: bool = OFFLINE_MODE_ENABLED

    MQTT_BROKER_HOST: str = MQTT_BROKER_HOST
    MQTT_BROKER_PORT: int = MQTT_BROKER_PORT
    MQTT_USERNAME: str = MQTT_USERNAME
    MQTT_PASSWORD: str = MQTT_PASSWORD

    LOG_LEVEL: str = LOG_LEVEL

settings = Settings()

# Example usage in other modules:
# from config import settings
# print(settings.OPENAI_API_KEY)
