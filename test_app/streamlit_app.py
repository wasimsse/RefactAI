import streamlit as st
import os
import requests
import json
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://86.50.169.115:11434")

def fetch_available_models():
    """Fetch available models from the Ollama server."""
    try:
        response = requests.get(f"{BASE_URL}/api/tags")
        
        if response.status_code == 200:
            models_data = response.json()
            # Convert the models data into a dictionary format
            available_models = {}
            for model in models_data.get("models", []):
                model_name = model.get("name", "")
                if model_name:  # Only add models with valid names
                    available_models[model_name] = model_name
            
            if not available_models:
                st.warning("No models were found on the Ollama server.")
                # Provide some default models that should be available
                available_models = {
                    "codellama:7b": "Code Llama 7B",
                    "codellama:13b": "Code Llama 13B",
                    "llama2:7b": "Llama 2 7B"
                }
            return available_models
        else:
            st.error(f"Failed to fetch models. Status code: {response.status_code}")
            st.error(f"Response: {response.text}")
            return {}
            
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return {}

def refactor_code(code, model_name):
    """Refactor code using the selected model."""
    # Prepare the prompt for code refactoring
    prompt = f"""You are an expert Java code refactoring assistant. Please refactor this Java code following these guidelines:
1. Apply SOLID principles
2. Improve code organization
3. Extract methods for readability
4. Use meaningful names
5. Add appropriate comments
6. Optimize performance
7. Handle edge cases
8. Follow Java best practices

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
    
    try:
        # Make the API request
        with st.spinner(f"Refactoring code using {model_name}..."):
            response = requests.post(
                f"{BASE_URL}/api/generate",
                json=payload
            )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            
            # Extract the refactored code from the response
            refactored_code = result.get("response", "")
            if not refactored_code:
                st.error("No refactored code was returned from the model.")
                return None
                
            return refactored_code
        else:
            st.error(f"Request failed with status code: {response.status_code}")
            st.error(f"Response: {response.text}")
            return None
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.title("RefactAI - Code Refactoring with Ollama")
    st.write("This app uses Ollama to refactor Java code.")
    
    # Display API configuration
    st.sidebar.header("API Configuration")
    st.sidebar.write(f"Ollama Server: {BASE_URL}")
    
    # Fetch available models
    available_models = fetch_available_models()
    
    if not available_models:
        st.error("No models available. Please check your connection to the Ollama server.")
        return
    
    # Sidebar for model selection
    st.sidebar.header("Model Selection")
    selected_model = st.sidebar.selectbox(
        "Select a model",
        options=list(available_models.keys()),
        index=0
    )
    
    # Display model information
    st.sidebar.header("Model Information")
    st.sidebar.write(f"Selected model: {selected_model}")
    
    # Main content
    st.header("Code Refactoring")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a Java file", type=["java"])
    
    # Text input for code
    code_input = st.text_area("Or paste Java code here", height=300)
    
    # Refactor button
    if st.button("Refactor Code"):
        # Get the code from either the uploaded file or text input
        code = ""
        if uploaded_file:
            code = uploaded_file.getvalue().decode()
        elif code_input:
            code = code_input
        else:
            st.warning("Please upload a Java file or paste Java code")
            return
        
        # Refactor the code
        refactored_code = refactor_code(code, selected_model)
        
        if refactored_code:
            # Display the refactored code
            st.header("Refactored Code")
            st.code(refactored_code, language="java")
            
            # Download button
            st.download_button(
                "Download Refactored Code",
                refactored_code,
                file_name="refactored_code.java",
                mime="text/plain"
            )
            
            # Save to session state
            st.session_state.refactored_code = refactored_code
            st.session_state.original_code = code
    
    # Display comparison if available
    if "refactored_code" in st.session_state and "original_code" in st.session_state:
        st.header("Code Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Code")
            st.code(st.session_state.original_code, language="java")
        
        with col2:
            st.subheader("Refactored Code")
            st.code(st.session_state.refactored_code, language="java")

if __name__ == "__main__":
    main() 