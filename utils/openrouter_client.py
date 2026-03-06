import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_VALIDATE_MODELS = os.getenv("OPENROUTER_VALIDATE_MODELS", "").lower() in {"1", "true", "yes"}
OPENROUTER_TIMEOUT_SECONDS = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))

_MODEL_CACHE = None


def _get_available_models():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    try:
        response = requests.get(f"{OPENROUTER_API_BASE}/models", timeout=OPENROUTER_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        _MODEL_CACHE = {item.get("id") for item in data.get("data", []) if item.get("id")}
        return _MODEL_CACHE
    except Exception as e:
        print(f"⚠️ OpenRouter Model List Error: {e}")
        _MODEL_CACHE = set()
        return _MODEL_CACHE

def call_openrouter(model, messages, enable_reasoning=False, api_key=None, response_format=None, plugins=None):
    """
    Generic wrapper for OpenRouter API.
    Supports the 'reasoning' parameter for models like GLM 4.5 Air and DeepSeek R1.
    If api_key is provided, use it; otherwise fall back to env var.
    """
    key = api_key or OPENROUTER_API_KEY

    if not key:
        print("❌ OpenRouter Error: Missing API key (set OPENROUTER_API_KEY or pass api_key).")
        return None

    if OPENROUTER_VALIDATE_MODELS:
        available = _get_available_models()
        if available and model not in available:
            print(f"⚠️ OpenRouter Warning: Model '{model}' not found in /models list.")
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", 
        "X-Title": "Darwinian Dialectics Agent",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    
    if enable_reasoning:
        payload["reasoning"] = {"enabled": True}
    if response_format:
        payload["response_format"] = response_format
    if plugins:
        # OpenRouter expects plugins as objects: [{ "id": "response-healing" }]
        normalized = []
        for plugin in plugins:
            if isinstance(plugin, str):
                normalized.append({"id": plugin})
            else:
                normalized.append(plugin)
        payload["plugins"] = normalized
        
    url = f"{OPENROUTER_API_BASE}/chat/completions"

    try:
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=OPENROUTER_TIMEOUT_SECONDS,
        )
        if not response.ok:
            body = response.text.strip()
            print(f"❌ OpenRouter Error {response.status_code} for {url} (model='{model}').")
            if body:
                # Avoid dumping huge bodies in logs.
                print(f"OpenRouter response: {body[:1000]}")
            return None
        return response.json()
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")
        return None
