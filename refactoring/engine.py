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
    """Engine for code refactoring using LLMs."""
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cpu"
        self.memory_config = {}
        self.logger = logging.getLogger(__name__)
    
    def _load_local_model(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """Load a local model with improved file handling and verification."""
        try:
            logger.info(f"Loading local model: {model_name}")
            
            # Set model name
            self.model_name = model_name
            
            # Map friendly model names to their IDs
            model_map = {
                "Code Llama 13B": "codellama/CodeLlama-13b-hf",
                "Code Llama 7B": "codellama/CodeLlama-7b-hf",
                "Code Llama 34B": "codellama/CodeLlama-34b-hf"
            }
            
            model_id = model_map.get(model_name)
            if not model_id:
                error_msg = f"Unknown model: {model_name}"
                logger.error(error_msg)
                return False, error_msg
            
            # Check model files
            model_path = Path("models") / model_name.lower().replace(" ", "-")
            config_file = model_path / "config.yaml"
            
            if not config_file.exists():
                error_msg = f"Config file not found: {config_file}"
                logger.error(error_msg)
                return False, error_msg
            
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
            except Exception as e:
                error_msg = f"Error loading config: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
            
            # Verify model files
            required_files = config.get("model_files", [])
            model_files = []
            for file in required_files:
                file_path = model_path / file
                if not file_path.exists():
                    error_msg = f"Model file not found: {file_path}"
                    logger.error(error_msg)
                    return False, error_msg
                model_files.append(file_path)
            
            # Load tokenizer with improved error handling
            try:
                logger.info("Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    str(model_path),
                    trust_remote_code=True,
                    use_fast=False  # Disable fast tokenizer for better compatibility
                )
                
                # Ensure pad token is set
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    logger.info("Set pad token to EOS token")
                
            except Exception as e:
                error_msg = f"Error loading tokenizer: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
            
            # Load model with improved memory handling
            try:
                logger.info("Loading model...")
                
                # Get device-specific configuration
                device = self.device
                if device == "mps":
                    logger.info("Using MPS-specific configuration")
                    # Force CPU memory for MPS
                    self.model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        torch_dtype=torch.float32,  # MPS requires float32
                        device_map=None,  # Manual device management
                        low_cpu_mem_usage=True,
                        trust_remote_code=True
                    )
                    # Move to MPS after loading
                    self.model = self.model.to(device)
                else:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        **self.memory_config,
                        trust_remote_code=True
                    )
                
                # Set model to evaluation mode
                self.model.eval()
                
                # Test model with a simple prompt
                test_prompt = "def hello():"
                inputs = self.tokenizer(test_prompt, return_tensors="pt").to(device)
                with torch.no_grad():
                    _ = self.model.generate(
                        inputs["input_ids"],
                        max_length=10,
                        temperature=0.7,
                        top_p=0.95
                    )
                
                logger.info(f"Model loaded successfully on {device}")
                return True, None
                
            except Exception as e:
                error_msg = f"Error loading model: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error in _load_local_model: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _load_cloud_model(self, model_name: str, api_key: Optional[str] = None) -> bool:
        """Load a cloud model."""
        try:
            if not api_key:
                self.logger.error("API key required for cloud models")
                return False
            
            self.api_key = api_key
            self.model_name = model_name
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading cloud model: {str(e)}")
            return False
            
    def load_model(self, source: str, model_name: str, api_key: Optional[str] = None, 
                  device: str = "cpu", **memory_config) -> Tuple[bool, Optional[str]]:
        """Load a model for code refactoring."""
        try:
            self.device = device
            self.memory_config = memory_config
            self.logger = logging.getLogger(__name__)
            
            # Log configuration
            self.logger.info(f"Loading model {model_name} from {source}")
            self.logger.info(f"Device: {device}")
            self.logger.info(f"Memory config: {memory_config}")
            
            # Normalize source
            source = source.lower()
            
            # Handle different model sources
            if source == "local":
                return self._load_local_model(model_name)
            elif source == "cloud":
                return self._load_cloud_model(model_name, api_key)
            else:
                return False, f"❌ Unknown model source: {source}"
                
        except Exception as e:
            self.logger.error(f"Error in load_model: {str(e)}", exc_info=True)
            return False, f"❌ Error in load_model: {str(e)}"
    
    def refactor_code(self, code: str, smells: List[str]) -> Tuple[str, Dict]:
        """Refactor code to address specified smells."""
        try:
            if not self.model or not self.tokenizer:
                raise RuntimeError("Model not loaded")
            
            # Create prompt
            prompt = self._create_refactoring_prompt(code, smells)
            
            # Generate refactored code
            if self.model_name.startswith("gpt") or self.model_name.startswith("claude"):
                return self._generate_cloud_refactoring(prompt)
            else:
                return self._generate_local_refactoring(prompt)
                
        except Exception as e:
            self.logger.error(f"Error during refactoring: {str(e)}")
            return code, {"error": str(e), "success": False}
    
    def _generate_local_refactoring(self, prompt: str) -> Tuple[str, Dict]:
        """Generate refactored code using local model."""
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate
            start_time = time.time()
            outputs = self.model.generate(
                **inputs,
                max_length=2048,
                temperature=0.7,
                top_p=0.95,
                do_sample=True
            )
            generation_time = time.time() - start_time
            
            # Decode output
            refactored_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract code from response
            code_match = re.search(r"```(?:java)?\n(.*?)\n```", refactored_code, re.DOTALL)
            if code_match:
                refactored_code = code_match.group(1).strip()
            
            return refactored_code, {
                "success": True,
                "generation_time": generation_time,
                "model": self.model_name,
                "device": self.device
            }
            
        except Exception as e:
            self.logger.error(f"Error in local generation: {str(e)}")
            return "", {"error": str(e), "success": False}
    
    def _generate_cloud_refactoring(self, prompt: str) -> Tuple[str, Dict]:
        """Generate refactored code using cloud API."""
        # Implementation depends on the cloud provider
        # This is a placeholder for the actual implementation
        return "", {"error": "Cloud generation not implemented", "success": False}
    
    def _create_refactoring_prompt(self, code: str, smells: List[str]) -> str:
        """Create a prompt for code refactoring."""
        smell_instructions = self._format_smell_instructions(smells)
        
        return f"""Please refactor the following Java code to address these code smells:
{smell_instructions}

Original code:
```java
{code}
```

Please provide the refactored code that:
1. Maintains the same functionality
2. Addresses the specified code smells
3. Follows Java best practices
4. Is well-documented

Refactored code:
```java
"""
    
    def _format_smell_instructions(self, smells: List[str]) -> str:
        """Format instructions for each code smell."""
        instructions = {
            "Long Method": "Break down the method into smaller, focused methods",
            "Large Class": "Split the class into smaller, cohesive classes",
            "Duplicate Code": "Extract common code into reusable methods",
            "Complex Conditionals": "Simplify complex if-else statements",
            "Dead Code": "Remove unused code and methods",
            "Magic Numbers": "Replace magic numbers with named constants",
            "Long Parameter List": "Use parameter objects to group related parameters"
        }
        
        return "\n".join(f"- {smell}: {instructions.get(smell, 'Improve code quality')}" for smell in smells) 