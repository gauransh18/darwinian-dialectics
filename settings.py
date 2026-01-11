# settings.py - User-configurable model and API key settings

# Default model configurations
DEFAULT_SETTINGS = {
    "api_key": "",  # Empty = use .env OPENROUTER_API_KEY
    "orchestrator_model": "xiaomi/mimo-v2-flash:free",
    "ingestion_model": "google/gemini-2.0-flash-exp:free",
    "coder_model": "deepseek/deepseek-v3.2",
    "auditor_model": "mistralai/devstral-2512:free"
}


def get_default_settings():
    """Return a copy of default settings."""
    return DEFAULT_SETTINGS.copy()
