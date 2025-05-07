import os
from openai import OpenAI
from typing import Dict, Optional, List, Tuple, Any
import logging
from dotenv import load_dotenv
import re
import yaml
from pathlib import Path
import requests

# Load environment variables
load_dotenv()

# Configure logging with more detail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPTlab Configuration
GPTLAB_API_KEY = os.getenv("GPTLAB_API_KEY")  # Changed from API_KEY_TOKEN
if not GPTLAB_API_KEY:
    logger.warning("No GPT-Lab API key found in environment variables. Some features may be limited.")
    GPTLAB_API_KEY = "sk-ollama-default"  # Default key for local testing

# Available GPTlab endpoints
GPTLAB_ENDPOINTS = {
    "GPU-farmi-001": {
        "url": "http://86.50.169.115:11434",  # Updated Ollama endpoint URL
        "hardware": "1xP40 + 1xL4",
        "description": "Primary GPU resource with P40 and L4",
        "status": "active"
    },
    "GPU-farmi-002": {
        "url": "http://86.50.169.115:11434",  # Updated Ollama endpoint URL
        "hardware": "1xP40",
        "description": "Secondary GPU resource with P40",
        "status": "active"
    },
    "CSC-P100": {
        "url": "http://86.50.169.115:11434",  # Updated Ollama endpoint URL
        "hardware": "1xP100",
        "description": "CSC resource with P100",
        "status": "active"
    },
    "RANDOM": {
        "url": "http://86.50.169.115:11434",  # Updated Ollama endpoint URL
        "hardware": "Various",
        "description": "Random selection of available resources",
        "status": "active"
    },
    "LOCAL": {
        "url": "http://86.50.169.115:11434",  # Updated Ollama endpoint URL
        "hardware": "Local CPU/GPU",
        "description": "Local Ollama instance",
        "status": "active"
    }
}

# Default models available on GPT-Lab
DEFAULT_MODELS = {
    "llama2": {
        "name": "llama2",
        "endpoint": "LOCAL",
        "hardware": "Local",
        "type": "local",
        "provider": "Ollama",
        "status": "available",
        "device": "Auto-selected",
        "max_tokens": 4096,
        "temperature": 0.3,
        "description": "Local Ollama model for code refactoring",
        "capabilities": ["code_refactoring", "code_analysis"],
        "version": "latest",
        "load": "N/A",
        "queue_length": 0
    }
}

def get_gptlab_client(endpoint: str = "LOCAL") -> OpenAI:
    """
    Get OpenAI client configured for GPT-Lab endpoint.
    
    Args:
        endpoint: Name of the endpoint to use
        
    Returns:
        OpenAI client instance
    """
    endpoint_info = GPTLAB_ENDPOINTS.get(endpoint)
    if not endpoint_info:
        logger.warning(f"Endpoint {endpoint} not found, using LOCAL")
        endpoint_info = GPTLAB_ENDPOINTS["LOCAL"]
        
    try:
        return OpenAI(
            api_key=GPTLAB_API_KEY,
            base_url=endpoint_info["url"]
        )
    except Exception as e:
        logger.error(f"Error creating OpenAI client for endpoint {endpoint}: {str(e)}")
        raise

def get_gptlab_models() -> Dict:
    """Return available GPTlab models from all endpoints."""
    all_models = {}
    
    try:
        # Get models from Ollama endpoint
        try:
            response = requests.get("http://86.50.169.115:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    model_name = model.get("name", "").split(":")[0]  # Remove version tag
                    if not model_name:
                        continue
                        
                    # Add model to each endpoint for availability
                    for endpoint_name, endpoint_info in GPTLAB_ENDPOINTS.items():
                        model_key = f"{model_name}@{endpoint_name}"
                        all_models[model_key] = {
                            "name": model_name,
                            "endpoint": endpoint_name,
                            "hardware": endpoint_info["hardware"],
                            "type": "cloud",
                            "provider": "Ollama",
                            "status": "available",
                            "device": endpoint_info["description"],
                            "max_tokens": 4096,
                            "temperature": 0.3,
                            "description": f"Ollama model on {endpoint_info['hardware']}",
                            "capabilities": ["code_refactoring", "code_analysis"],
                            "version": model.get("details", {}).get("parameter_size", "unknown"),
                            "load": "N/A",
                            "queue_length": 0
                        }
                logger.info(f"Found {len(models)} models from Ollama endpoint")
            else:
                logger.error(f"Error fetching models from Ollama endpoint: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama endpoint: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error discovering models: {e}")
        return {}
        
    # If no models found, return default models
    if not all_models:
        logger.warning("No models found from endpoints, using defaults")
        return DEFAULT_MODELS
    
    return all_models

def normalize_model_name(model_name: str) -> str:
    """
    Convert external model name to GPT-Lab compatible name.
    """
    if not model_name:
        return "llama2"
        
    # Remove any path components and file extensions
    base_name = os.path.basename(model_name).split('.')[0].lower()
    
    # Remove version numbers and special characters
    base_name = re.sub(r'[:\-]', '', base_name)
    base_name = re.sub(r'\d+\.\d+', '', base_name)
    
    # Map to available GPT-Lab models
    model_mapping = {
        "qwen": "qwen",
        "qwen2": "qwen",
        "qwen25": "qwen",
        "qwen14b": "qwen",
        "codellama": "codellama",
        "code": "codellama",
        "mistral": "mistral",
        "phi": "phi-2",
        "phi2": "phi-2",
        "llama": "llama2",
        "llama2": "llama2",
        "llama3": "llama2"
    }
    
    # Try exact match first
    if base_name in model_mapping:
        return model_mapping[base_name]
        
    # Try partial match
    for key, value in model_mapping.items():
        if key in base_name or base_name in key:
            return value
            
    # Default to llama2 if no match found
    return "llama2"

def refactor_with_gptlab(
    code: str, 
    model_name: str, 
    endpoint: str,
    smell_analysis: Dict[str, Any],
    additional_instructions: str = ""
) -> str:
    """
    Refactor code using Ollama API based on detected code smells.
    """
    try:
        # Build a comprehensive refactoring prompt
        smell_instructions = []
        if smell_analysis:
            detected_smells = smell_analysis.get("smells", [])
            metrics = smell_analysis.get("metrics", {})
            reasoning = smell_analysis.get("reasoning", {})
            metrics_evidence = smell_analysis.get("evidence", {})
            
            for smell in detected_smells:
                smell_instructions.append(f"""
Code Smell: {smell}
Reason: {reasoning.get(smell, 'No specific reason provided')}
Evidence: {metrics_evidence.get(smell, 'No specific metrics evidence')}
""")
        
        # Build the base prompt
        base_prompt = f"""Please refactor the following Java code to address specific code smells detected by our analysis.

{chr(10).join(smell_instructions) if smell_instructions else "No specific smells detected. Focus on general code quality improvement."}

Code Metrics:
{chr(10).join(f'- {metric}: {value}' for metric, value in metrics.items()) if smell_analysis and metrics else "No metrics provided"}

Additional Requirements:
1. Focus on improving code quality and readability
2. Maintain the original functionality
3. Preserve test compatibility
4. Document changes inline
5. Keep the code style consistent
{f'6. {additional_instructions}' if additional_instructions else ''}

Original Code:
```java
{code}
```

Please provide:
1. The refactored code with inline comments explaining changes
2. A brief summary of improvements made
3. Any potential impact on performance or functionality"""

        # Make API request to Ollama
        response = requests.post(
            "http://86.50.169.115:11434/api/generate",
            json={
                "model": model_name,
                "prompt": base_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 4096
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error from Ollama API: {response.status_code}")
            return code
            
        # Extract refactored code from response
        response_json = response.json()
        response_text = response_json.get("response", "")
        
        # Extract code block if present
        code_pattern = r"```java\n(.*?)```"
        matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        else:
            logger.warning("No code block found in response")
            return response_text
            
    except Exception as e:
        error_msg = f"Error during refactoring: {str(e)}"
        logger.error(error_msg)
        return code

def check_ollama_status(endpoint: str = "LOCAL") -> bool:
    """Check if the Ollama endpoint is available."""
    try:
        response = requests.get("http://86.50.169.115:11434/api/tags")
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Failed to get status for Ollama endpoint: {str(e)}")
        return False 