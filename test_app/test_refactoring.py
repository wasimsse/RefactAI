import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from pathlib import Path
import sys
import os
import time
import signal
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test code sample
TEST_CODE = """
public class Calculator {
    private int result;
    
    public int add(int a, int b) {
        result = a + b;
        return result;
    }
    
    public int subtract(int a, int b) {
        result = a - b;
        return result;
    }
    
    public int multiply(int a, int b) {
        result = a * b;
        return result;
    }
    
    public int divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        result = a / b;
        return result;
    }
}
"""

# Timeout settings (in seconds)
GENERATION_TIMEOUT = 60  # 1 minute timeout for generation
MODEL_LOAD_TIMEOUT = 120  # 2 minutes timeout for model loading

@contextmanager
def timeout(seconds):
    """Context manager for timing out operations."""
    def signal_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and a timeout
    original_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the original signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

def test_model_refactoring(model_name, model_path):
    """Test a model's refactoring capabilities."""
    try:
        logger.info(f"Testing {model_name}...")
        
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

Please provide the complete refactored code with explanations of the changes made.""",

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
I'll help you refactor this code. First, let me analyze the code and provide a summary of improvements, then I'll show you the refactored code.""",

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

Please provide the complete refactored code with explanations of the changes made.""",

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
I'll help you refactor this code. First, let me analyze the code and provide a summary of improvements, then I'll show you the refactored code."""
        }
        
        # Get model-specific prompt
        prompt = prompts.get(model_name, prompts["CodeGemma 2B"]).format(code=TEST_CODE)
        
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
        
        # Get model-specific settings
        settings = generation_settings.get(model_name, generation_settings["CodeGemma 2B"])
        
        # Load tokenizer
        logger.info(f"Loading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side="left",
            truncation_side="left"
        )
        
        # Add special tokens for Qwen if needed
        if "qwen" in model_name.lower():
            special_tokens = {
                "additional_special_tokens": [
                    "<|im_start|>",
                    "<|im_end|>",
                    "<|im_sep|>",
                    "<|im_continue|>"
                ]
            }
            tokenizer.add_special_tokens(special_tokens)
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        
        # Load model with timeout
        logger.info(f"Loading model {model_name}...")
        try:
            with timeout(MODEL_LOAD_TIMEOUT):
                # Check if flash_attn is available
                try:
                    import flash_attn
                    use_flash_attention = True
                    logger.info("FlashAttention2 is available and will be used")
                except ImportError:
                    use_flash_attention = False
                    logger.warning("FlashAttention2 is not available. Using standard attention instead.")
                
                # Configure model loading
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
                
                # Resize token embeddings if needed
                if "qwen" in model_name.lower():
                    model.resize_token_embeddings(len(tokenizer))
        except TimeoutError:
            logger.error(f"Model loading timed out after {MODEL_LOAD_TIMEOUT} seconds")
            return False
        
        # Tokenize input
        logger.info("Tokenizing input...")
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(model.device)
        
        # Generate refactored code with timeout
        logger.info("Generating refactored code...")
        start_time = time.time()
        try:
            with timeout(GENERATION_TIMEOUT):
                outputs = model.generate(
                    **inputs,
                    **settings,
                    do_sample=True,
                    num_return_sequences=1,
                    pad_token_id=tokenizer.eos_token_id,
                    length_penalty=1.0,
                    no_repeat_ngram_size=3
                )
        except TimeoutError:
            logger.error(f"Generation timed out after {GENERATION_TIMEOUT} seconds")
            return False
        
        generation_time = time.time() - start_time
        logger.info(f"Generation completed in {generation_time:.2f} seconds")
        
        # Decode output
        refactored_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Save output
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{model_name.lower().replace(' ', '_')}_refactored.txt"
        with open(output_file, "w") as f:
            f.write(refactored_text)
        
        logger.info(f"Test completed for {model_name}")
        logger.info(f"Output saved to {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing {model_name}: {str(e)}")
        return False

def main():
    """Run tests for all available models."""
    models_dir = Path("models")
    
    # Test each model
    for model_dir in models_dir.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name.replace('-', ' ').title()
            test_model_refactoring(model_name, model_dir)

if __name__ == "__main__":
    main() 