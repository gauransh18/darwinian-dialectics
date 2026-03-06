# settings.py - User-configurable model and API key settings

# Default model configurations
DEFAULT_SETTINGS = {
    "api_key": "",  # Empty = use .env OPENROUTER_API_KEY
    "orchestrator_model": "z-ai/glm-4.5-air:free",
    "ingestion_model": "arcee-ai/trinity-large-preview:free",
    "coder_model": "stepfun/step-3.5-flash:free",
    "auditor_model": "nvidia/nemotron-3-nano-30b-a3b:free",
    "general_model": "arcee-ai/trinity-large-preview:free"
}


def get_default_settings():
    """Return a copy of default settings."""
    return DEFAULT_SETTINGS.copy()
