import os
import requests
from typing import Dict, Optional, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPTlab Configuration - Use environment variables with secure defaults
GPTLAB_BASE_URL = os.getenv("GPTLAB_BASE_URL", "http://localhost:11434")  # Default to local Ollama
GPTLAB_API_KEY = os.getenv("GPTLAB_API_KEY", "")  # No default API key for security

def get_gptlab_models() -> Dict:
    """Fetch available models from the GPTlab/Ollama server."""
    try:
        if not GPTLAB_BASE_URL:
            logger.error("GPTLAB_BASE_URL not configured")
            return _get_fallback_models()

        # Make request to list available models - using Ollama's API endpoint
        logger.info(f"Attempting to fetch models from server")
        response = requests.get(f"{GPTLAB_BASE_URL}/api/tags")
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch models. Status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return _get_fallback_models()
            
        models_data = response.json()
        available_models = {}
        
        # Process models from Ollama response
        for model in models_data.get("models", []):
            model_name = model.get("name", "")
            if not model_name:
                continue
                
            # Convert model name to a more readable format
            display_name = model_name.replace(":", " ").title()
            
            available_models[display_name] = {
                "name": model_name,
                "type": "cloud",
                "provider": "gptlab",
                "status": "available",
                "max_tokens": 2048,
                "temperature": 0.3
            }
        
        if not available_models:
            logger.warning("No models found in server response, using fallback models")
            return _get_fallback_models()
        
        logger.info(f"Successfully found {len(available_models)} models")
        return available_models
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return _get_fallback_models()
    except Exception as e:
        logger.error(f"Unexpected error fetching models: {str(e)}")
        return _get_fallback_models()

def _get_fallback_models() -> Dict:
    """Return fallback models when server connection fails."""
    logger.info("Using fallback models")
    return {
        "Code Llama 7B": {
            "name": "codellama:7b",
            "type": "cloud",
            "provider": "gptlab",
            "status": "available",
            "max_tokens": 2048,
            "temperature": 0.3
        },
        "Code Llama 13B": {
            "name": "codellama:13b",
            "type": "cloud",
            "provider": "gptlab",
            "status": "available",
            "max_tokens": 2048,
            "temperature": 0.3
        },
        "Llama 2 7B": {
            "name": "llama2:7b",
            "type": "cloud",
            "provider": "gptlab",
            "status": "available",
            "max_tokens": 2048,
            "temperature": 0.3
        }
    }

def refactor_with_gptlab(code: str, model_name: str, smells: Optional[List[str]] = None) -> str:
    """Refactor code using GPTlab/Ollama models."""
    try:
        if not GPTLAB_BASE_URL:
            logger.error("GPTLAB_BASE_URL not configured")
            return None

        # Prepare the prompt
        prompt = f"""You are an expert Java code refactoring assistant. Please refactor this Java code following these guidelines:
1. Apply SOLID principles
2. Improve code organization
3. Extract methods for readability
4. Use meaningful names
5. Add appropriate comments
6. Optimize performance
7. Handle edge cases
8. Follow Java best practices

{"Code smells to address:" + ", ".join(smells) if smells else ""}

Here's the code to refactor:
{code}

Please provide the complete refactored code with explanations of the changes made."""

        # Prepare the request payload for Ollama
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.95,
                "num_predict": 2048
            }
        }

        logger.info(f"Sending refactoring request for model: {model_name}")
        # Make the API request to Ollama
        headers = {"Authorization": f"Bearer {GPTLAB_API_KEY}"} if GPTLAB_API_KEY else {}
        response = requests.post(
            f"{GPTLAB_BASE_URL}/api/generate",
            json=payload,
            headers=headers
        )

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            refactored_code = result.get("response", "")
            if not refactored_code:
                logger.error("Empty response from model")
                return None
            return refactored_code
        else:
            logger.error(f"API request failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error in refactoring: {str(e)}")
        return None 