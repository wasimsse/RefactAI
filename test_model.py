from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

def test_codellama():
    # Initialize tokenizer and model from Hugging Face
    model_name = "codellama/CodeLlama-7b-hf"
    
    print(f"\nTesting CodeLlama model...")
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print(f"Loading model {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Test prompt
    prompt = """
    # Write a Python function to check if a string is a palindrome
    def is_palindrome(s):
    """
    
    print("\nGenerating code with CodeLlama...")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        inputs["input_ids"],
        max_length=200,
        temperature=0.2,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\nGenerated code:")
    print(response)

def test_starcoder():
    # Initialize tokenizer and model from Hugging Face
    model_name = "bigcode/starcoderbase"
    
    # Create offload directory if it doesn't exist
    offload_folder = "offload"
    os.makedirs(offload_folder, exist_ok=True)
    
    print(f"\nTesting StarCoder model...")
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print(f"Loading model {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,  # Required for StarCoder
        offload_folder=offload_folder  # Specify offload directory for large model
    )
    
    # Test prompt
    prompt = """
    # Write a Python function to check if a string is a palindrome
    def is_palindrome(s):
    """
    
    print("\nGenerating code with StarCoder...")
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        inputs["input_ids"],
        max_length=200,
        temperature=0.2,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\nGenerated code:")
    print(response)

if __name__ == "__main__":
    # Test both models
    test_codellama()
    test_starcoder() 