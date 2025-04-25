import streamlit as st
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODELS_DIR = Path("../models")
UPLOADS_DIR = Path("uploads")
RESULTS_DIR = Path("results")

# Available models configuration
AVAILABLE_MODELS = {
    "CodeGemma 2B": {
        "path": MODELS_DIR / "codegemma-2b",
        "repo_id": "google/codegemma-2b"
    },
    "Code Llama 7B": {
        "path": MODELS_DIR / "codellama-7b",
        "repo_id": "codellama/CodeLlama-7b-hf"
    },
    "DeepSeek Coder 6.7B": {
        "path": MODELS_DIR / "deepseek-coder-6.7b",
        "repo_id": "deepseek-ai/deepseek-coder-6.7b-base"
    },
    "StarCoder2 3B": {
        "path": MODELS_DIR / "starcoder2-3b",
        "repo_id": "bigcode/starcoder2-3b"
    },
    "Qwen2.5-Coder 3B": {
        "path": MODELS_DIR / "qwen2.5-coder-3b",
        "repo_id": "Qwen/Qwen2.5-Coder-3B"
    }
}

def initialize_session_state():
    """Initialize session state variables."""
    if "model" not in st.session_state:
        st.session_state.model = None
    if "tokenizer" not in st.session_state:
        st.session_state.tokenizer = None
    if "current_model_name" not in st.session_state:
        st.session_state.current_model_name = None
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

def load_model(model_name):
    """Load the selected model and tokenizer."""
    try:
        model_config = AVAILABLE_MODELS[model_name]
        model_path = model_config["path"]
        
        logger.info(f"Loading model: {model_name}")
        logger.info(f"Model path: {model_path}")
        
        # Check if model files exist
        if not model_path.exists():
            st.error(f"Model files not found at {model_path}")
            return False
        
        # Model-specific configurations
        if "starcoder" in model_name.lower():
            # Special configuration for StarCoder2
            tokenizer = AutoTokenizer.from_pretrained(
                "bigcode/starcoder2-3b",
                trust_remote_code=True,
                padding_side="left",
                truncation_side="left"
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                "bigcode/starcoder2-3b",
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
        elif "qwen" in model_name.lower():
            # Special configuration for Qwen2.5-Coder
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                padding_side="left",
                truncation_side="left"
            )
            
            # Add special tokens for Qwen
            special_tokens = {
                "additional_special_tokens": [
                    "<|im_start|>",
                    "<|im_end|>",
                    "<|im_sep|>",
                    "<|im_continue|>"
                ]
            }
            tokenizer.add_special_tokens(special_tokens)
            
            # Check if flash_attn is available
            try:
                import flash_attn
                use_flash_attention = True
                logger.info("FlashAttention2 is available and will be used")
            except ImportError:
                use_flash_attention = False
                logger.warning("FlashAttention2 is not available. Using standard attention instead.")
            
            # Configure model loading based on flash_attn availability
            model_kwargs = {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "trust_remote_code": True,
                "low_cpu_mem_usage": True
            }
            
            if use_flash_attention:
                model_kwargs["attn_implementation"] = "flash_attention_2"
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs
            )
            
            # Resize token embeddings to account for new tokens
            model.resize_token_embeddings(len(tokenizer))
        else:
            # Load tokenizer with special token handling
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                padding_side="left",
                truncation_side="left"
            )
            
            # Set pad token if not set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.pad_token_id = tokenizer.eos_token_id
            
            # Configure model loading based on model type
            model_kwargs = {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "trust_remote_code": True,
                "low_cpu_mem_usage": True
            }
            
            # Load model with optimizations
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **model_kwargs
            )
        
        # Update session state
        st.session_state.model = model
        st.session_state.tokenizer = tokenizer
        st.session_state.current_model_name = model_name
        
        # Log success
        logger.info(f"Successfully loaded {model_name}")
        logger.info(f"Model device: {model.device}")
        logger.info(f"Tokenizer vocabulary size: {len(tokenizer)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        st.error(f"Error loading model: {str(e)}")
        return False

def refactor_code(code, model_name):
    """Perform code refactoring using the selected model."""
    try:
        if not st.session_state.model or not st.session_state.tokenizer:
            st.error("Please load a model first")
            return None
            
        # Model-specific prompts
        prompts = {
            "CodeGemma 2B": """You are an expert Java code refactoring assistant. Please refactor the following Java code to improve its quality, maintainability, and readability. Follow these guidelines:

1. Apply SOLID principles where applicable
2. Improve code organization and structure
3. Extract methods for better readability
4. Use meaningful variable and method names
5. Add appropriate comments for complex logic
6. Optimize performance where possible
7. Handle edge cases and add proper error handling
8. Follow Java best practices and coding standards

Original code:
{code}

Please provide the complete refactored code with explanations of the changes made. Start with a brief summary of the improvements, followed by the refactored code.

Summary of improvements:""",

            "DeepSeek Coder 6.7B": """<|im_start|>system
You are an expert Java code refactoring assistant. Your task is to refactor the provided Java code to improve its quality, maintainability, and readability.
<|im_end|>
<|im_start|>user
Please refactor this Java code following these guidelines:
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
<|im_end|>
<|im_start|>assistant
I'll help you refactor this code. First, let me analyze the code and provide a summary of improvements, then I'll show you the refactored code.

Summary of improvements:""",

            "StarCoder2 3B": """<|endoftext|>You are an expert Java code refactoring assistant. Please refactor the following Java code to improve its quality, maintainability, and readability. Follow these guidelines:

1. Apply SOLID principles where applicable
2. Improve code organization and structure
3. Extract methods for better readability
4. Use meaningful variable and method names
5. Add appropriate comments for complex logic
6. Optimize performance where possible
7. Handle edge cases and add proper error handling
8. Follow Java best practices and coding standards

Original code:
{code}

Please provide the complete refactored code with explanations of the changes made. Start with a brief summary of the improvements, followed by the refactored code.

Summary of improvements:""",

            "Qwen2.5-Coder 3B": """<|im_start|>system
You are an expert Java code refactoring assistant. Your task is to refactor the provided Java code to improve its quality, maintainability, and readability.
<|im_end|>
<|im_start|>user
Please refactor this Java code following these guidelines:
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
<|im_end|>
<|im_start|>assistant
I'll help you refactor this code. First, let me analyze the code and provide a summary of improvements, then I'll show you the refactored code.

Summary of improvements:"""
        }
        
        # Get model-specific prompt or use default
        prompt = prompts.get(model_name, prompts["CodeGemma 2B"]).format(code=code)
        
        # Model-specific generation settings
        generation_settings = {
            "CodeGemma 2B": {
                "max_new_tokens": 2048,
                "temperature": 0.3,
                "top_p": 0.95,
                "repetition_penalty": 1.2
            },
            "DeepSeek Coder 6.7B": {
                "max_new_tokens": 2048,
                "temperature": 0.2,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            },
            "StarCoder2 3B": {
                "max_new_tokens": 2048,
                "temperature": 0.3,
                "top_p": 0.95,
                "repetition_penalty": 1.2
            },
            "Qwen2.5-Coder 3B": {
                "max_new_tokens": 2048,
                "temperature": 0.2,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        }
        
        # Get model-specific settings or use default
        settings = generation_settings.get(model_name, generation_settings["CodeGemma 2B"])
        
        # Tokenize input with proper padding
        inputs = st.session_state.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(st.session_state.model.device)
        
        # Generate refactored code with model-specific settings
        outputs = st.session_state.model.generate(
            **inputs,
            **settings,
            do_sample=True,
            num_return_sequences=1,
            pad_token_id=st.session_state.tokenizer.eos_token_id,
            length_penalty=1.0,
            no_repeat_ngram_size=3
        )
        
        # Decode and extract refactored code
        refactored_text = st.session_state.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the refactored code part
        try:
            # Try to find the code block after the summary
            code_start = refactored_text.find("```java")
            if code_start == -1:
                code_start = refactored_text.find("```")
            if code_start == -1:
                code_start = refactored_text.find("Refactored code:")
            
            if code_start != -1:
                # Extract everything after the code block marker
                refactored_code = refactored_text[code_start:]
                # Remove markdown code block markers if present
                refactored_code = refactored_code.replace("```java", "").replace("```", "").strip()
            else:
                # Fallback: take everything after the summary
                refactored_code = refactored_text.split("Summary of improvements:")[-1].strip()
            
            # Clean up the code
            refactored_code = refactored_code.replace("Refactored code:", "").strip()
            
            return refactored_code
            
        except Exception as e:
            logger.error(f"Error extracting refactored code: {str(e)}")
            return refactored_text  # Return full response if extraction fails
        
    except Exception as e:
        logger.error(f"Error during refactoring: {str(e)}")
        st.error(f"Error during refactoring: {str(e)}")
        return None

def main():
    st.title("Code Refactoring Model Tester")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for model selection and loading
    with st.sidebar:
        st.header("Model Selection")
        
        # Model selection dropdown
        selected_model = st.selectbox(
            "Select a model",
            options=list(AVAILABLE_MODELS.keys()),
            index=None,
            placeholder="Choose a model..."
        )
        
        # Load model button
        if st.button("Load Model"):
            if selected_model:
                with st.spinner(f"Loading {selected_model}..."):
                    if load_model(selected_model):
                        st.success(f"Successfully loaded {selected_model}")
                    else:
                        st.error(f"Failed to load {selected_model}")
            else:
                st.warning("Please select a model first")
        
        # Display current model status
        if st.session_state.current_model_name:
            st.info(f"Current model: {st.session_state.current_model_name}")
            
        # Display model capabilities
        st.header("Model Capabilities")
        st.markdown("""
        - Code refactoring
        - SOLID principles application
        - Code organization
        - Performance optimization
        - Error handling
        - Best practices implementation
        """)
    
    # Main content area
    st.header("Code Refactoring")
    
    # File upload
    uploaded_file = st.file_uploader("Upload a Java file", type=["java"])
    
    if uploaded_file:
        # Save uploaded file
        file_path = UPLOADS_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file = file_path
        
        # Create two columns for side-by-side comparison
        col1, col2 = st.columns(2)
        
        # Display original code
        with col1:
            st.subheader("Original Code")
            code = uploaded_file.getvalue().decode()
            st.code(code, language="java")
        
        # Refactor button
        if st.button("Refactor Code"):
            if not st.session_state.model:
                st.error("Please load a model first")
            else:
                with st.spinner("Refactoring code..."):
                    refactored_code = refactor_code(code, st.session_state.current_model_name)
                    
                    if refactored_code:
                        # Save refactored code
                        result_path = RESULTS_DIR / f"refactored_{uploaded_file.name}"
                        with open(result_path, "w") as f:
                            f.write(refactored_code)
                        
                        # Display refactored code
                        with col2:
                            st.subheader("Refactored Code")
                            st.code(refactored_code, language="java")
                            
                        # Download button
                        st.download_button(
                            "Download Refactored Code",
                            refactored_code,
                            file_name=f"refactored_{uploaded_file.name}",
                            mime="text/plain"
                        )
                        
                        # Show comparison
                        st.header("Code Comparison")
                        st.info("""
                        The refactored code has been generated with the following improvements:
                        - Enhanced code organization and structure
                        - Improved naming conventions
                        - Better error handling
                        - Optimized performance
                        - Added documentation
                        - Applied SOLID principles
                        """)

if __name__ == "__main__":
    main() 