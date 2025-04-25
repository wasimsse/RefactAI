import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY", "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM/v1")

# Test code for refactoring
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

def test_ollama_api(model_name="codellama:7b"):
    """Test the Ollama API with a specific model."""
    print(f"Testing Ollama API with model: {model_name}")
    print(f"Base URL: {BASE_URL}")
    
    # Prepare the prompt for code refactoring
    prompt = f"""You are an expert Java code refactoring assistant. Please refactor the following Java code to improve its quality, maintainability, and readability. Follow these guidelines:

1. Apply SOLID principles where applicable
2. Improve code organization and structure
3. Extract methods for better readability
4. Use meaningful variable and method names
5. Add appropriate comments for complex logic
6. Optimize performance where possible
7. Handle edge cases and add proper error handling
8. Follow Java best practices and coding standards

Original code:
{TEST_CODE}

Please provide the complete refactored code with explanations of the changes made."""
    
    # Prepare the request payload
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        # Make the API request
        print("Sending request to Ollama API...")
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("Request successful!")
            
            # Extract and print the refactored code
            refactored_code = result.get("response", "")
            print("\nRefactored Code:")
            print(refactored_code)
            
            # Save the result to a file
            with open(f"test_results/{model_name.replace(':', '_')}_refactored.txt", "w") as f:
                f.write(refactored_code)
            print(f"\nResult saved to test_results/{model_name.replace(':', '_')}_refactored.txt")
            
            return True
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_chat_completion(model_name="codellama:7b"):
    """Test the chat completion API with a specific model."""
    print(f"Testing Chat Completion API with model: {model_name}")
    print(f"Base URL: {BASE_URL}")
    
    # Prepare the messages for code refactoring
    messages = [
        {
            "role": "system",
            "content": "You are an expert Java code refactoring assistant. Your task is to refactor the provided Java code to improve its quality, maintainability, and readability."
        },
        {
            "role": "user",
            "content": f"""Please refactor this Java code following these guidelines:
1. Apply SOLID principles
2. Improve code organization
3. Extract methods for readability
4. Use meaningful names
5. Add appropriate comments
6. Optimize performance
7. Handle edge cases
8. Follow Java best practices

Here's the code to refactor:
{TEST_CODE}"""
        }
    ]
    
    # Prepare the request payload
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    
    try:
        # Make the API request
        print("Sending request to Chat Completion API...")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("Request successful!")
            
            # Extract and print the refactored code
            refactored_code = result.get("message", {}).get("content", "")
            print("\nRefactored Code:")
            print(refactored_code)
            
            # Save the result to a file
            with open(f"test_results/{model_name.replace(':', '_')}_chat_refactored.txt", "w") as f:
                f.write(refactored_code)
            print(f"\nResult saved to test_results/{model_name.replace(':', '_')}_chat_refactored.txt")
            
            return True
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Run tests with different models."""
    # Create test_results directory if it doesn't exist
    os.makedirs("test_results", exist_ok=True)
    
    # List of models to test
    models = [
        "codellama:7b",
        "codegemma:7b",
        "deepseek-coder:6.7b",
        "starcoder2:3b",
        "qwen2.5-coder:3b"
    ]
    
    # Test each model
    for model in models:
        print("\n" + "="*50)
        print(f"Testing model: {model}")
        print("="*50)
        
        # Test with completion API
        test_ollama_api(model)
        
        # Test with chat completion API
        test_chat_completion(model)

if __name__ == "__main__":
    main() 