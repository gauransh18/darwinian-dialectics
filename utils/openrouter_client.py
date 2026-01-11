import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(model, messages, enable_reasoning=False, api_key=None):
    """
    Generic wrapper for OpenRouter API.
    Supports the 'reasoning' parameter for models like Xiaomi MiMo and DeepSeek R1.
    If api_key is provided, use it; otherwise fall back to env var.
    """
    key = api_key or OPENROUTER_API_KEY
    
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
        
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")
        return None