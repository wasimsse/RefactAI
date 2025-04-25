"""
Handles prompt creation, model interaction, and LLM responses for code refactoring.
"""
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import os
from pathlib import Path
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import psutil
import logging
from abc import ABC, abstractmethod
import yaml
import time
import re
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelRunner(ABC):
    """Abstract base class for model runners."""
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the model."""
        pass
    
    @abstractmethod
    def run_inference(self, prompt: str) -> Tuple[str, Dict]:
        """Run model inference."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """Get model status."""
        pass

class LocalModelRunner(ModelRunner):
    """Handles local model inference using HuggingFace Transformers."""
    def __init__(self, model_path: str, model_config: Dict):
        self.model_path = Path(model_path)
        self.config = model_config
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.last_ping = None
        
        # Set model-specific parameters
        self.max_tokens = model_config.get("max_tokens", 4096)
        self.temperature = model_config.get("temperature", 0.7)
        self.top_p = model_config.get("top_p", 0.95)
        self.torch_dtype = getattr(torch, model_config.get("torch_dtype", "float16"))
        self.device_map = model_config.get("device_map", "auto")
    
    def initialize(self) -> bool:
        try:
            logger.info(f"Initializing model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=self.torch_dtype,
                device_map=self.device_map,
                trust_remote_code=True
            )
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Test model with a simple prompt
            test_prompt = "def hello():"
            inputs = self.tokenizer(test_prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                _ = self.model.generate(
                    inputs["input_ids"],
                    max_length=10,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
            
            self.last_ping = time.time()
            logger.info(f"Model initialized successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing local model: {e}")
            return False
    
    def run_inference(self, prompt: str) -> Tuple[str, Dict]:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            inference_time = time.time() - start_time
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract code between ```java and ``` tags
            code_match = re.search(r"```java\n(.*?)\n```", generated_text, re.DOTALL)
            refactored_code = code_match.group(1).strip() if code_match else generated_text
            
            metadata = {
                "inference_time": inference_time,
                "device": self.device,
                "memory_usage": self._get_memory_usage(),
                "prompt_tokens": len(inputs["input_ids"][0]),
                "completion_tokens": len(outputs[0]) - len(inputs["input_ids"][0])
            }
            
            return refactored_code, metadata
            
        except Exception as e:
            logger.error(f"Error during local inference: {e}")
            raise
    
    def get_status(self) -> Dict:
        if not self.model:
            return {"status": "offline", "icon": "❌"}
        
        try:
            # Test if model is responsive
            _ = self.tokenizer.encode("test", return_tensors="pt")
            self.last_ping = time.time()
            
            return {
                "status": "active",
                "icon": "✅",
                "device": self.device,
                "memory_usage": self._get_memory_usage(),
                "last_ping": self.last_ping
            }
        except:
            return {"status": "error", "icon": "🟡"}
    
    def _get_memory_usage(self) -> Dict:
        try:
            if self.device == "cuda":
                return {
                    "gpu_allocated": torch.cuda.memory_allocated() / 1024**3,
                    "gpu_reserved": torch.cuda.memory_reserved() / 1024**3
                }
            else:
                process = psutil.Process(os.getpid())
                return {"ram_usage": process.memory_info().rss / 1024**3}
        except:
            return {}

class CloudModelRunner(ModelRunner):
    """Handles cloud-based model inference (e.g., OpenAI, Mistral)."""
    def __init__(self, api_config: Dict):
        self.config = api_config
        self.api_key = None
        self.base_url = api_config.get("base_url", "https://api.example.com/v1")
        self.last_ping = None
    
    def initialize(self) -> bool:
        try:
            self.api_key = os.getenv("LLM_API_KEY")
            if not self.api_key:
                return False
            
            # Test connection
            response = self._make_request("GET", "/models")
            self.last_ping = time.time()
            return True
        except Exception as e:
            logger.error(f"Error initializing cloud model: {e}")
            return False
    
    def run_inference(self, prompt: str) -> Tuple[str, Dict]:
        try:
            start_time = time.time()
            response = self._make_request(
                "POST",
                "/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "stop": ["```"]
                }
            )
            inference_time = time.time() - start_time
            
            refactored_code = response.json()["choices"][0]["text"]
            metadata = {
                "inference_time": inference_time,
                "token_usage": response.json().get("usage", {})
            }
            
            return refactored_code, metadata
            
        except Exception as e:
            logger.error(f"Error during cloud inference: {e}")
            raise
    
    def get_status(self) -> Dict:
        try:
            response = self._make_request("GET", "/models")
            self.last_ping = time.time()
            return {
                "status": "active",
                "icon": "✅",
                "last_ping": self.last_ping
            }
        except:
            return {"status": "offline", "icon": "❌"}
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with proper headers and error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        return response

class ModelRegistry:
    """Manages available models and their configurations."""
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models: Dict[str, Dict] = {}
        self.runners: Dict[str, ModelRunner] = {}
        self._scan_models()
    
    def _scan_models(self):
        """Scan for available models and validate them."""
        logger.info(f"Scanning for models in {self.models_dir}")
        
        # Scan local models
        if self.models_dir.exists():
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir():
                    config_file = model_dir / "config.yaml"
                    if config_file.exists():
                        try:
                            with open(config_file) as f:
                                config = yaml.safe_load(f)
                            
                            # Validate required fields
                            required_fields = ["name", "type", "model_type", "tokenizer_type"]
                            missing_fields = [field for field in required_fields if field not in config]
                            if missing_fields:
                                logger.error(f"Missing required fields in {config_file}: {missing_fields}")
                                continue
                            
                            model_id = config["name"]
                            
                            # Check if model files exist
                            model_files = list(model_dir.glob("*.bin")) + list(model_dir.glob("*.pt"))
                            if not model_files:
                                logger.error(f"No model files found in {model_dir}")
                                continue
                            
                            # Add model to registry
                            self.models[model_id] = {
                                "path": str(model_dir),
                                "type": "local",
                                "config_file": str(config_file),
                                "model_files": [str(f) for f in model_files],
                                **config
                            }
                            logger.info(f"Added model: {model_id}")
                            
                        except Exception as e:
                            logger.error(f"Error loading model config {config_file}: {e}")
        
        # Add cloud model configurations
        cloud_models = {
            "gpt-4-turbo": {
                "type": "cloud",
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "max_tokens": 4096,
                "model_type": "gpt-4",
                "tokenizer_type": "gpt-4"
            },
            "mistral-large": {
                "type": "cloud",
                "provider": "mistral",
                "base_url": "https://api.mistral.ai/v1",
                "max_tokens": 8192,
                "model_type": "mistral-large",
                "tokenizer_type": "mistral-large"
            }
        }
        self.models.update(cloud_models)
        logger.info(f"Found {len(self.models)} models: {list(self.models.keys())}")
    
    def get_model_runner(self, model_id: str) -> Optional[ModelRunner]:
        """Get or create a model runner for the specified model."""
        if model_id not in self.models:
            logger.error(f"Model {model_id} not found in registry")
            return None
        
        if model_id not in self.runners:
            model_config = self.models[model_id]
            try:
                if model_config["type"] == "local":
                    self.runners[model_id] = LocalModelRunner(
                        model_config["path"],
                        model_config
                    )
                    logger.info(f"Created LocalModelRunner for {model_id}")
                elif model_config["type"] == "cloud":
                    self.runners[model_id] = CloudModelRunner(model_config)
                    logger.info(f"Created CloudModelRunner for {model_id}")
            except Exception as e:
                logger.error(f"Error creating model runner for {model_id}: {e}")
                return None
        
        return self.runners[model_id]
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get information about all available models."""
        model_info = {}
        for model_id, config in self.models.items():
            runner = self.get_model_runner(model_id)
            if runner:
                status = runner.get_status()
                model_info[model_id] = {
                    **config,
                    **status
                }
        return model_info

class RefactoringEngine:
    """Engine for code refactoring using language models."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = None
        self.api_key = None
        self.source = None
        
    def load_model(self, source: str, model_name: str, api_key: Optional[str] = None, device: str = "cpu") -> Tuple[bool, str]:
        """Load a model from the specified source."""
        try:
            self.source = source
            self.model_name = model_name
            self.device = device
            self.api_key = api_key
            
            if source == "Local":
                return self._load_local_model()
            elif source in ["Cloud", "Private Cloud"]:
                return self._load_cloud_model()
            else:
                return False, f"Invalid source: {source}"
                
        except Exception as e:
            error_msg = f"Error loading model: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _load_local_model(self) -> Tuple[bool, str]:
        """Load a local model."""
        try:
            # Map model names to HuggingFace model IDs
            model_mapping = {
                "Code Llama 7B": "TheBloke/CodeLlama-7B-Python-GGUF",
                "Code Llama 13B": "TheBloke/CodeLlama-13B-Python-GGUF"
            }
            
            model_id = model_mapping.get(self.model_name)
            if not model_id:
                return False, f"Unknown model: {self.model_name}"
            
            # Check for HF token
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                return False, "Hugging Face token not found. Please set HF_TOKEN environment variable."
            
            # Configure model loading
            config = {
                "device_map": "auto" if self.device == "cuda" else None,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "low_cpu_mem_usage": True,
                "trust_remote_code": True
            }
            
            # Load tokenizer
            self.logger.info(f"Loading tokenizer for {model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                token=hf_token,
                trust_remote_code=True
            )
            
            # Load model
            self.logger.info(f"Loading model {model_id} on {self.device}")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                token=hf_token,
                **config
            )
            
            # Move model to device if needed
            if self.device == "mps":
                self.model = self.model.to("mps")
            elif self.device == "cpu":
                self.model = self.model.to("cpu")
            
            self.logger.info(f"Model {self.model_name} loaded successfully")
            return True, "Model loaded successfully"
            
        except Exception as e:
            error_msg = f"Error loading local model: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _load_cloud_model(self) -> Tuple[bool, str]:
        """Load a cloud model configuration."""
        try:
            if not self.api_key:
                return False, "API key required for cloud models"
            
            # Just set the API key for cloud models
            os.environ[f"{self.source.upper()}_API_KEY"] = self.api_key
            return True, "Cloud model configured successfully"
            
        except Exception as e:
            error_msg = f"Error configuring cloud model: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def refactor_code(self, code: str, smells: List[str]) -> Tuple[str, Dict]:
        """Refactor code using the loaded model."""
        try:
            # Check model state
            if self.source == "local":
                if not self.model or not self.tokenizer:
                    raise RuntimeError("Model or tokenizer not loaded. Please load a model first.")
            elif self.source in ["cloud", "private cloud"]:
                if not self.api_key:
                    raise RuntimeError("API key not set for cloud model.")
            else:
                raise RuntimeError(f"Invalid model source: {self.source}")

            # Create refactoring prompt
            prompt = self._create_refactoring_prompt(code, smells)
            
            # Generate refactored code
            if self.source == "local":
                refactored_code = self._generate_local(prompt)
            else:
                refactored_code = self._generate_cloud(prompt)
            
            # Extract code and metadata
            result = self._extract_code_from_response(refactored_code)
            
            # Return results
            return result["code"], {
                "model": self.model_name,
                "source": self.source,
                "smells_addressed": smells,
                "changes": result.get("changes", []),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            error_msg = f"Error during refactoring: {str(e)}"
            self.logger.error(error_msg)
            return code, {
                "error": error_msg,
                "model": self.model_name,
                "source": self.source,
                "smells_addressed": smells
            }

    def _generate_local(self, prompt: str) -> str:
        """Generate code using local model."""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=4096,
                    temperature=0.7,
                    top_p=0.95,
                    do_sample=True,
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
        except Exception as e:
            raise RuntimeError(f"Error in local generation: {str(e)}")

    def _generate_cloud(self, prompt: str) -> str:
        """Generate code using cloud API."""
        try:
            # Configure API client based on source
            if self.source == "cloud":
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4096
                )
                return response.choices[0].message.content
            else:  # private cloud
                # Add implementation for private cloud API
                raise NotImplementedError("Private cloud API not implemented yet")
                
        except Exception as e:
            raise RuntimeError(f"Error in cloud generation: {str(e)}")

    def _extract_code_from_response(self, response: str) -> Dict:
        """Extract code and metadata from model response."""
        try:
            # Initialize result
            result = {
                "code": "",
                "changes": [],
                "reasoning": ""
            }
            
            # Extract code block
            code_pattern = r"```(?:java)?\n(.*?)```"
            code_matches = re.findall(code_pattern, response, re.DOTALL)
            
            if code_matches:
                result["code"] = code_matches[0].strip()
            else:
                # Fallback: try to extract any code-like content
                lines = response.split("\n")
                code_lines = []
                in_code = False
                
                for line in lines:
                    if line.strip().startswith("public") or line.strip().startswith("private") or line.strip().startswith("class"):
                        in_code = True
                    if in_code:
                        code_lines.append(line)
                
                if code_lines:
                    result["code"] = "\n".join(code_lines)
                else:
                    result["code"] = response  # Use full response if no code found
            
            # Extract reasoning (if any)
            reasoning_pattern = r"(?:Reasoning|Changes made|Explanation):(.*?)(?:```|$)"
            reasoning_match = re.search(reasoning_pattern, response, re.DOTALL | re.IGNORECASE)
            if reasoning_match:
                result["reasoning"] = reasoning_match.group(1).strip()
            
            # Extract changes (if any)
            changes_pattern = r"(?:Changes|Modifications):\s*\n((?:[-*]\s*[^\n]+\n)*)"
            changes_match = re.search(changes_pattern, response, re.IGNORECASE)
            if changes_match:
                changes = re.findall(r"[-*]\s*([^\n]+)", changes_match.group(1))
                result["changes"] = changes
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Error extracting code from response: {str(e)}")
            return {"code": response, "changes": [], "reasoning": ""}

    def _create_refactoring_prompt(self, code: str, smells: List[str]) -> str:
        """Create a detailed prompt for code refactoring."""
        smell_instructions = self._format_smell_instructions(smells)
        
        return f"""You are an expert Java developer tasked with refactoring code to improve its quality.
Please analyze and refactor the following Java code to address these code smells:

{smell_instructions}

Original code:
```java
{code}
```

Please provide a refactored version that:
1. Maintains the exact same functionality and behavior
2. Addresses each identified code smell using appropriate refactoring patterns
3. Follows Java best practices and design principles
4. Is well-documented with clear comments explaining complex logic
5. Uses meaningful variable and method names
6. Has proper error handling and input validation
7. Is modular and follows the Single Responsibility Principle

For each refactoring change, please:
1. Explain the specific changes made to address each smell
2. Describe the refactoring patterns used
3. Highlight any potential impacts on other parts of the codebase

Refactored code:
```java
"""
    
    def _format_smell_instructions(self, smells: List[str]) -> str:
        """Format detailed instructions for each code smell."""
        instructions = {
            "God Class": """- God Class: The class is too large and has too many responsibilities
  * Split the class into smaller, focused classes
  * Extract related functionality into separate classes
  * Use composition to delegate responsibilities
  * Consider applying the Single Responsibility Principle""",
            
            "Data Class": """- Data Class: The class primarily holds data with minimal behavior
  * Add meaningful behavior to the class
  * Consider making it a proper DTO if it's meant for data transfer
  * Add validation and business logic where appropriate
  * Consider using the Builder pattern for complex object creation""",
            
            "Lazy Class": """- Lazy Class: The class has too little responsibility
  * Consider merging with parent class if inheritance is appropriate
  * Move functionality to a more appropriate class
  * Remove the class if it's truly unnecessary
  * Consider using composition instead""",
            
            "Feature Envy": """- Feature Envy: Methods use more features of other classes than their own
  * Move the method to the class it's most interested in
  * Consider using the Move Method refactoring pattern
  * Evaluate if the method belongs in a different class
  * Use composition to access needed functionality""",
            
            "Refused Bequest": """- Refused Bequest: The class inherits but doesn't use inherited behavior
  * Consider composition over inheritance
  * Remove unused inherited methods
  * Create a new base class with only the needed functionality
  * Use interfaces instead of inheritance where appropriate""",
            
            "Long Method": """- Long Method: The method is too long and complex
  * Break down into smaller, focused methods
  * Extract repeated code into helper methods
  * Use meaningful method names that describe their purpose
  * Consider using the Extract Method refactoring pattern""",
            
            "Complex Conditionals": """- Complex Conditionals: The code has complex if-else statements
  * Use guard clauses to handle edge cases early
  * Extract complex conditions into well-named methods
  * Consider using the Strategy pattern for complex logic
  * Use switch statements or pattern matching where appropriate"""
        }
        
        return "\n\n".join(instructions.get(smell, f"- {smell}: Improve code quality and maintainability") for smell in smells) 