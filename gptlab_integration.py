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
GPTLAB_API_KEY = os.getenv("API_KEY_TOKEN", "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d")

# Available GPTlab endpoints
GPTLAB_ENDPOINTS = {
    "GPU-farmi-001": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-001/",
        "hardware": "1xP40 + 1xL4",
        "description": "Primary GPU resource with P40 and L4",
        "status": "active"
    },
    "GPU-farmi-002": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/GPU-farmi-002/",
        "hardware": "1xP40",
        "description": "Secondary GPU resource with P40",
        "status": "active"
    },
    "CSC": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/CSC-P100/",
        "hardware": "1xP100",
        "description": "CSC resource with P100",
        "status": "active"
    },
    "RANDOM": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM/",
        "hardware": "Various",
        "description": "Random selection of available resources",
        "status": "active"
    },
    "LOCAL": {
        "url": "http://localhost:11434/v1",
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
        
    return OpenAI(
        api_key=GPTLAB_API_KEY,
        base_url=endpoint_info["url"]
    )

def get_gptlab_models() -> Dict:
    """
    Return available GPTlab models from all endpoints.
    """
    all_models = {}
    
    # Check each endpoint
    for endpoint_name, endpoint_info in GPTLAB_ENDPOINTS.items():
        try:
            client = get_gptlab_client(endpoint_name)
            
            # Get models from this endpoint
            try:
                models = client.models.list()
                
                # Add models with endpoint information
                for model in models.data:  # Use .data for Ollama response
                    model_id = getattr(model, 'id', None)
                    if not model_id:
                        continue
                        
                    model_key = f"{model_id}@{endpoint_name}"
                    
                    # For Ollama models, use default values
                    if endpoint_name == "LOCAL":
                        all_models[model_key] = {
                            "name": model_id,
                            "endpoint": endpoint_name,
                            "hardware": endpoint_info["hardware"],
                            "type": "local",
                            "provider": "Ollama",
                            "status": "available",
                            "device": endpoint_info["description"],
                            "max_tokens": 4096,  # Default for Ollama
                            "temperature": 0.3,
                            "description": f"Local Ollama model",
                            "capabilities": ["code_refactoring", "code_analysis"],
                            "version": "latest",
                            "load": "N/A",
                            "queue_length": 0
                        }
                    else:
                        # For GPT-Lab models
                        all_models[model_key] = {
                            "name": model_id,
                            "endpoint": endpoint_name,
                            "hardware": endpoint_info["hardware"],
                            "type": "cloud",
                            "provider": "GPTlab",
                            "status": "available",
                            "device": endpoint_info["description"],
                            "max_tokens": getattr(model, 'max_tokens', 4096),
                            "temperature": 0.3,
                            "description": f"GPTlab model on {endpoint_info['hardware']}",
                            "capabilities": ["code_refactoring", "code_analysis"],
                            "version": "latest",
                            "load": "N/A",
                            "queue_length": 0
                        }
                
                logger.info(f"Found {len(models.data)} models on endpoint {endpoint_name}")
                
            except Exception as e:
                logger.error(f"Error fetching models from endpoint {endpoint_name}: {str(e)}")
                continue
                
        except Exception as e:
            logger.error(f"Error connecting to endpoint {endpoint_name}: {str(e)}")
            continue
    
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
    Refactor code using GPT-Lab API based on detected code smells.
    """
    try:
        # Get GPT-Lab client
        client = get_gptlab_client(endpoint)
        
        # Normalize model name
        model = normalize_model_name(model_name)
        
        # Extract smell information
        detected_smells = smell_analysis.get("smells", [])
        metrics = smell_analysis.get("metrics", {})
        reasoning = smell_analysis.get("reasoning", {})
        metrics_evidence = smell_analysis.get("evidence", {})
        
        # Build a comprehensive refactoring prompt
        smell_instructions = []
        for smell in detected_smells:
            smell_instructions.append(f"""
Code Smell: {smell}
Reason: {reasoning.get(smell, 'No specific reason provided')}
Evidence: {metrics_evidence.get(smell, 'No specific metrics evidence')}
""")
        
        # Build the base prompt
        base_prompt = f"""Please refactor the following Java code to address specific code smells detected by our analysis.

Detected Code Smells and Analysis:
{chr(10).join(smell_instructions)}

Code Metrics:
{chr(10).join(f'- {metric}: {value}' for metric, value in metrics.items())}

Additional Requirements:
1. Focus ONLY on fixing the detected code smells
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
1. The refactored code with inline comments explaining smell-related changes
2. A brief summary of how each detected smell was addressed
3. Any potential impact on performance or functionality"""

        # Make API request
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": base_prompt
            }],
            temperature=0.2,
            max_tokens=4096
        )
        
        # Extract refactored code from response
        response_text = response.choices[0].message.content
        
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
        return f"Error: {error_msg}"

def check_ollama_status(endpoint: str = "LOCAL") -> bool:
    """
    Check if the specified endpoint is available.
    
    Args:
        endpoint: Name of the endpoint to check
        
    Returns:
        bool: True if endpoint is available, False otherwise
    """
    try:
        endpoint_info = GPTLAB_ENDPOINTS.get(endpoint)
        if not endpoint_info:
            logger.warning(f"Endpoint {endpoint} not found")
            return False
            
        # For local Ollama endpoint
        if endpoint == "LOCAL":
            response = requests.get("http://localhost:11434/api/tags")
            return response.status_code == 200
            
        # For remote GPT-Lab endpoints
        else:
            response = requests.get(f"{endpoint_info['url']}health")
            return response.status_code == 200
            
    except Exception as e:
        logger.warning(f"Failed to get status for endpoint {endpoint}: {str(e)}")
        return False 