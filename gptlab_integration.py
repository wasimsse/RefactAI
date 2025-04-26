import os
import requests
from typing import Dict, Optional, List, Tuple
import logging
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPTlab Configuration
GPTLAB_API_KEY = os.getenv("API_KEY_TOKEN", "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d")

# Available GPTlab endpoints
GPTLAB_ENDPOINTS = {
    "GPU-farmi-001": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-001",
        "hardware": "1xP40 + 1xL4",
        "description": "High-performance dual GPU setup"
    },
    "RANDOM": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM",
        "hardware": "Various",
        "description": "Automatically selects available resources"
    }
}

# Default models available on Ollama
AVAILABLE_MODELS = [
    "llama3.2",
    "codellama",
    "mistral",
    "qwen",
    "phi-2"
]

def get_available_models_from_server(endpoint_url: str) -> Dict[str, str]:
    """Fetch actual model names from the server."""
    try:
        headers = {"Authorization": f"Bearer {GPTLAB_API_KEY}"}
        response = requests.get(f"{endpoint_url}/api/tags", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            models = {}
            for model in data.get("models", []):
                name = model.get("name")
                if name:
                    models[name.lower()] = name
            logger.info(f"Retrieved {len(models)} models from server")
            return models
        else:
            logger.error(f"Failed to get models from server: {response.status_code}")
            return {"llama3.2": "llama3.2"}  # Fallback to default model
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        return {"llama3.2": "llama3.2"}  # Fallback to default model

def normalize_model_name(model_name: str) -> str:
    """Convert external model names to Ollama compatible names."""
    try:
        # Remove any path components and clean the name
        base_name = model_name.split('/')[-1].lower()
        base_name = re.sub(r'[-_.]', '', base_name)
        base_name = base_name.replace('gguf', '').replace('bin', '')
        base_name = base_name.replace('instruct', '')
        
        # Map model names to Ollama versions
        if "qwen" in base_name:
            return "llama3.2"  # Fallback for Qwen models
        elif "codellama" in base_name:
            return "codellama"
        elif "llama" in base_name:
            return "llama3.2"
        elif "mistral" in base_name:
            return "mistral"
        elif "phi" in base_name:
            return "phi-2"
        
        # Default fallback
        logger.warning(f"No specific mapping found for {model_name}, using llama3.2")
        return "llama3.2"
        
    except Exception as e:
        logger.error(f"Error normalizing model name: {str(e)}")
        return "llama3.2"

def refactor_with_gptlab(code: str, model_name: str, endpoint: str, smells: Optional[List[str]] = None) -> str:
    """Refactor code using GPTlab Ollama API."""
    try:
        endpoint_info = GPTLAB_ENDPOINTS.get(endpoint)
        if not endpoint_info:
            logger.error(f"Invalid endpoint: {endpoint}")
            return None

        base_url = endpoint_info["url"]
        
        # Normalize the model name to Ollama compatible format
        ollama_model = normalize_model_name(model_name)
        logger.info(f"Using Ollama model: {ollama_model}")

        # Prepare the prompt
        smell_specific_instructions = ""
        if smells:
            smell_specific_instructions = "\nSpecific code smells to address:\n"
            for smell in smells:
                if smell == "God Class":
                    smell_specific_instructions += "- Break down large class into smaller, focused classes\n"
                elif smell == "Complex Class":
                    smell_specific_instructions += "- Simplify complex logic and reduce cyclomatic complexity\n"
                elif smell == "Feature Envy":
                    smell_specific_instructions += "- Move methods to more appropriate classes\n"
                elif smell == "Data Class":
                    smell_specific_instructions += "- Add behavior to data-only classes\n"
                elif smell == "Long Method":
                    smell_specific_instructions += "- Break down long methods into smaller, focused methods\n"

        prompt = f"""You are an expert Java code refactoring assistant. Please refactor this Java code following these guidelines:
1. Apply SOLID principles
2. Improve code organization
3. Extract methods for readability
4. Use meaningful names
5. Add appropriate comments
6. Optimize performance
7. Handle edge cases
8. Follow Java best practices

{smell_specific_instructions}

Here's the code to refactor:
{code}

Please provide ONLY the refactored code without any explanations or comments about the changes."""

        # Make the API request using Ollama's API format
        headers = {"Authorization": f"Bearer {GPTLAB_API_KEY}"}
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.95,
                "num_ctx": 4096
            }
        }

        logger.info(f"Making request to {base_url}/api/generate")
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            refactored_code = result.get("response", "")
            
            if not refactored_code:
                logger.error("Empty response from model")
                return None
            
            # Clean up the response
            refactored_code = refactored_code.strip()
            if refactored_code.startswith("```java"):
                refactored_code = refactored_code[7:]
            if refactored_code.endswith("```"):
                refactored_code = refactored_code[:-3]
            
            return refactored_code.strip()
        else:
            error_msg = f"API request failed: {response.status_code}"
            if response.text:
                try:
                    error_details = response.json()
                    error_msg += f"\nDetails: {error_details}"
                except:
                    error_msg += f"\nResponse: {response.text[:200]}"
            logger.error(error_msg)
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error in refactoring: {str(e)}")
        return None 

def get_gptlab_models() -> Dict:
    """Return available GPTlab models."""
    try:
        # Try to get models from the default endpoint
        endpoint_info = GPTLAB_ENDPOINTS["GPU-farmi-001"]
        base_url = endpoint_info["url"]
        
        # Make request to list available models
        headers = {"Authorization": f"Bearer {GPTLAB_API_KEY}"}
        response = requests.get(f"{base_url}/api/tags", headers=headers)
        
        if response.status_code == 200:
            models_data = response.json()
            available_models = {}
            
            # Process models from response
            for model in models_data.get("models", []):
                model_name = model.get("name", "")
                if not model_name:
                    continue
                
                # Extract model size and type
                size_match = re.search(r'(\d+)b', model_name.lower())
                size_str = f"{size_match.group(1)}B" if size_match else "Unknown"
                
                # Determine model capabilities
                capabilities = ["code_refactoring", "code_analysis"]
                if "code" in model_name.lower() or "llama" in model_name.lower():
                    capabilities.extend(["advanced_patterns", "complex_refactoring"])
                
                available_models[model_name] = {
                    "name": model_name,
                    "endpoint": "GPU-farmi-001",
                    "hardware": endpoint_info["hardware"],
                    "type": "cloud",
                    "provider": "GPTlab",
                    "status": "available",
                    "device": endpoint_info["description"],
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "description": f"GPTlab {size_str} model on {endpoint_info['hardware']}",
                    "capabilities": capabilities,
                    "version": "latest"
                }
            
            if available_models:
                logger.info(f"Found {len(available_models)} models")
                return available_models
                
        # If no models found or error occurred, return default models
        return {
            "llama3.2": {
                "name": "llama3.2",
                "endpoint": "RANDOM",
                "hardware": "Various",
                "type": "cloud",
                "provider": "GPTlab",
                "status": "available",
                "device": "Auto-selected GPU",
                "max_tokens": 4096,
                "temperature": 0.3,
                "description": "Llama 3.2 model for code refactoring",
                "capabilities": ["code_refactoring", "code_analysis"],
                "version": "latest"
            },
            "codellama": {
                "name": "codellama",
                "endpoint": "GPU-farmi-001",
                "hardware": "1xP40 + 1xL4",
                "type": "cloud",
                "provider": "GPTlab",
                "status": "available",
                "device": "High-performance dual GPU setup",
                "max_tokens": 4096,
                "temperature": 0.3,
                "description": "CodeLlama model for advanced code refactoring",
                "capabilities": ["code_refactoring", "code_analysis", "advanced_patterns"],
                "version": "latest"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        return {} 