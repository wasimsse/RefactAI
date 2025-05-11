"""
Integration module for GPT-Lab API and local model interactions.
"""
import os
import requests
import json
from typing import Dict, List, Optional, Any
import logging
import streamlit as st
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GPTLAB_ENDPOINTS = {
    "LOCAL": {
        "url": "http://localhost:11434",
        "hardware": "Local CPU/GPU",
        "status": "active"
    },
    "CLOUD": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM/v1",
        "hardware": "Cloud GPU",
        "status": "active"
    }
}
GPTLAB_BEARER_TOKEN = "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d"

DEFAULT_MODELS = {
    "llama3.2": {"type": "local", "provider": "Ollama"},
    "llama3.1:70b-instruct-q4_K_M": {"type": "local", "provider": "Ollama"},
    "codellama:7b": {"type": "local", "provider": "Ollama"},
    "codegemma:7b": {"type": "local", "provider": "Ollama"},
    "deepseek-coder:6.7b": {"type": "local", "provider": "Ollama"},
    "phi4:14b-fp16": {"type": "local", "provider": "Ollama"},
    "GPT-Lab/Viking-33B-cp2000B-GGUF:Q6_K": {"type": "cloud", "provider": "GPT-Lab"},
    "magicoder:7b": {"type": "local", "provider": "Ollama"}
}

def get_gptlab_client(api_key: Optional[str] = None) -> 'GPTLabClient':
    """Get a configured GPT-Lab client."""
    return GPTLabClient(api_key)

def check_ollama_status(endpoint: str = "LOCAL") -> bool:
    """Check if Ollama service is running at the specified endpoint."""
    try:
        if endpoint == "LOCAL":
            response = requests.get("http://localhost:11434/api/tags")
            return response.status_code == 200
        else:
            # For cloud endpoints, assume they're active
            return True
    except:
        return False

def get_gptlab_models() -> Dict[str, Any]:
    """Get available models from GPT-Lab."""
    return DEFAULT_MODELS

def normalize_model_name(model_name: str) -> str:
    """Normalize model name to standard format."""
    return model_name.lower().replace(" ", "-")

def gptlab_chat(prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 4096, **kwargs) -> str:
    """
    Send a chat request to either local Ollama or GPT-Lab cloud.
    
    Args:
        prompt: The input prompt
        model: Model name to use
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate (default: 4096)
        **kwargs: Additional parameters for the model
    """
    try:
        if DEFAULT_MODELS.get(model, {}).get("type") == "local":
            # Use local Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise Exception(f"Ollama request failed: {response.text}")
        else:
            # Use GPT-Lab cloud
            client = get_gptlab_client()
            return client.chat(prompt, model, temperature=temperature, max_tokens=max_tokens, **kwargs)
            
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise

class GPTLabClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GPTLAB_BEARER_TOKEN
        self.base_url = GPTLAB_ENDPOINTS["CLOUD"]["url"]
    
    def chat(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 4096, **kwargs) -> str:
        """Send a chat request to GPT-Lab API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API request failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error in GPT-Lab chat: {str(e)}")
            raise

    def completions(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 4096, **kwargs) -> str:
        """Send a completion request to GPT-Lab API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            response = requests.post(
                f"{self.base_url}/completions",
                headers=headers,
                json=data
            )
            if response.status_code == 200:
                # The response format may differ; adjust as needed
                return response.json()["choices"][0]["text"]
            else:
                raise Exception(f"API request failed: {response.text}")
        except Exception as e:
            logger.error(f"Error in GPT-Lab completions: {str(e)}")
            raise

def refactor_with_gptlab(
    code: str,
    model_name: str,
    endpoint: str = "CLOUD",
    smell_analysis: Optional[Dict] = None,
    additional_instructions: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.3
) -> str:
    """
    Refactor code using GPT-Lab cloud model.
    """
    try:
        prompt = f"""Please refactor the following code{' according to the analysis and instructions below' if smell_analysis or additional_instructions else ''}:

{code}

"""
        if smell_analysis:
            prompt += f"\nCode Smell Analysis:\n{json.dumps(smell_analysis, indent=2)}\n"
        if additional_instructions:
            prompt += f"\nAdditional Instructions:\n{additional_instructions}\n"
        prompt += "\nPlease provide the refactored code with explanations of the changes made."
        client = GPTLabClient()
        return client.completions(prompt, model_name, temperature=temperature, max_tokens=max_tokens)
    except Exception as e:
        logger.error(f"Error in refactoring: {str(e)}")
        raise

def render_refactoring_preview(original_code, refactored_code):
    """
    Display a unified diff between the original and refactored code.
    """
    diff = difflib.unified_diff(
        original_code.splitlines(),
        refactored_code.splitlines(),
        fromfile='Original',
        tofile='Refactored',
        lineterm=''
    )
    diff_text = '\n'.join(diff)
    if diff_text.strip():
        st.code(diff_text, language="diff")
    else:
        st.info("No changes detected between the original and refactored code.")

def generate_refactoring(original_code, selected_patterns, detected_smells):
    """
    Generate refactored code using GPT-Lab or local LLM.
    Returns (refactored_code, metadata).
    """
    if not selected_patterns:
        st.warning("No patterns selected for refactoring.")
        return original_code, {"success": False, "reason": "No patterns selected."}
    instructions = f"Apply the following refactoring patterns: {', '.join(selected_patterns)}."
    try:
        st.info(f"Calling LLM with model: {st.session_state.get('current_model', 'llama3.2')}")
        st.info(f"Patterns: {selected_patterns}")
        st.info(f"Detected smells: {detected_smells}")
        model_to_use = st.session_state.get('selected_model', DEFAULT_MODELS.keys()[0])
        refactored_code = refactor_with_gptlab(
            code=original_code,
            model_name=model_to_use,
            smell_analysis=detected_smells,
            additional_instructions=instructions,
            temperature=st.session_state.get('refactoring_sidebar_temperature', 0.3)
        )
        st.success("LLM call completed.")
        return refactored_code, {"success": True, "patterns": selected_patterns}
    except Exception as e:
        st.error(f"Refactoring failed: {e}")
        return original_code, {"success": False, "reason": str(e)}

# Export all required functions and constants
__all__ = [
    'get_gptlab_client',
    'GPTLAB_ENDPOINTS',
    'DEFAULT_MODELS',
    'refactor_with_gptlab',
    'check_ollama_status',
    'get_gptlab_models',
    'normalize_model_name',
    'gptlab_chat'
] 