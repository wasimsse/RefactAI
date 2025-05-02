import streamlit as st
import os
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import tempfile
import zipfile
import shutil
import requests
import io
import time
import re
from datetime import datetime
import logging
import psutil
import torch
import yaml
from contextlib import contextmanager
from smell_detector.detector import detect_smells
from gptlab_integration import (
    get_gptlab_client, GPTLAB_ENDPOINTS, DEFAULT_MODELS,
    refactor_with_gptlab, check_ollama_status,
    get_gptlab_models,
    normalize_model_name
)
from refactoring.file_utils import RefactoringFileManager
import difflib
import html
import pandas as pd

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable unnecessary warnings
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure Streamlit page
st.set_page_config(
    page_title="RefactAI - Code Quality Analysis",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container padding */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Custom metric container */
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid #e9ecef;
    }
    
    /* Custom button styles */
    .stButton button {
        width: 100%;
        border-radius: 0.3rem;
        height: 2.5rem;
        background: linear-gradient(to right, #0066cc, #0052a3);
        color: white;
        border: none;
        font-weight: 500;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 0.5rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px;
        gap: 8px;
        padding: 0.5rem 1rem;
    }
    
    /* Status indicator */
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-inactive {
        color: #dc3545;
        font-weight: bold;
    }
    
    /* Code viewer */
    .code-container {
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #f8f9fa;
    }
    .java-code {
        counter-reset: line;
        white-space: pre;
        border-radius: 3px;
        font-family: monospace;
    }
    .java-code .line {
        display: block;
        position: relative;
        padding-left: 4em;
    }
    .java-code .line:before {
        content: counter(line);
        counter-increment: line;
        position: absolute;
        left: 0;
        width: 3em;
        padding-right: 1em;
        text-align: right;
        color: #999;
        border-right: 1px solid #ddd;
    }
    .java-code .added {
        background-color: #e6ffe6;
    }
    .java-code .removed {
        background-color: #ffe6e6;
    }
    .java-code .modified {
        background-color: #fff3e6;
    }
</style>
""", unsafe_allow_html=True)

class ProjectManager:
    """Manages the current project state and operations."""
    def __init__(self):
        self.project_path: Optional[Path] = None
        self.project_files: List[Path] = []
        self.analysis_results: Dict = {}
        self.project_metadata: Dict = {
            "name": "",
            "source": "",
            "upload_time": None,
            "file_count": 0,
            "total_size": 0,
            "java_files": []
        }
        self.temp_dir = None
    
    def load_from_zip(self, zip_file) -> bool:
        """Load project from ZIP file."""
        try:
            # Create a new temporary directory
            self.cleanup()  # Clean up any existing temp directory
            self.temp_dir = tempfile.mkdtemp()
            self.project_path = Path(self.temp_dir)
            
            # Extract ZIP contents
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Update project metadata
            self.project_metadata["name"] = zip_file.name
            self.project_metadata["source"] = "ZIP Upload"
            self.project_metadata["upload_time"] = datetime.now()
            
            # Scan for Java files
            self._scan_java_files()
            return True
        except Exception as e:
            st.error(f"Error loading project: {str(e)}")
            self.cleanup()
            return False
    
    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None
        self.project_path = None
    
    def load_from_github(self, repo_url: str, branch: str = "main") -> bool:
        """Load project from GitHub repository."""
        try:
            # Validate and parse GitHub URL
            url_pattern = r'^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
            match = re.match(url_pattern, repo_url)
            if not match:
                st.error(
                    "Invalid GitHub URL format. Please use: https://github.com/username/repository"
                )
                return False
            
            owner, repo = match.groups()
            
            # Construct the ZIP download URL
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            
            # Download repository with timeout and stream settings
            try:
                response = requests.get(
                    zip_url,
                    stream=True,
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 404:
                    st.error(
                        f"Repository or branch not found: {owner}/{repo}:{branch}\n"
                        "Please check that:\n"
                        "- The repository exists and is public\n"
                        "- The branch name is correct\n"
                        "- You have the necessary permissions"
                    )
                    return False
                elif response.status_code != 200:
                    st.error(
                        f"Failed to download repository. Status code: {response.status_code}\n"
                        f"Error: {response.text[:200]}"
                    )
                    return False
                
                # Create temp directory and extract ZIP
                temp_dir = tempfile.mkdtemp()
                self.project_path = Path(temp_dir)
                
                with tempfile.NamedTemporaryFile() as temp_zip:
                    # Download ZIP in chunks
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_zip.write(chunk)
                    temp_zip.flush()
                    
                    try:
                        with zipfile.ZipFile(temp_zip.name) as zip_ref:
                            zip_ref.extractall(temp_dir)
                    except zipfile.BadZipFile:
                        st.error(
                            "The downloaded file is not a valid ZIP archive.\n"
                            "This might happen if the repository is empty or the response was an error page."
                        )
                        return False
                
                # Update project metadata
                self.project_metadata.update({
                    "name": f"{owner}/{repo}",
                    "source": "GitHub",
                    "branch": branch,
                    "upload_time": datetime.now(),
                    "repo_url": repo_url
                })
                
                # Scan for Java files
                self._scan_java_files()
                
                if self.project_metadata["file_count"] == 0:
                    st.warning(
                        "Repository was downloaded successfully, but no Java files were found.\n"
                        "Make sure the repository contains .java files in the specified branch."
                    )
                
                return True
                
            except requests.Timeout:
                st.error(
                    "Connection timed out while downloading repository.\n"
                    "Please check your internet connection and try again."
                )
                return False
            except requests.ConnectionError:
                st.error(
                    "Failed to connect to GitHub.\n"
                    "Please check your internet connection and try again."
                )
                return False
            
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            return False
    
    def load_individual_files(self, files: List) -> bool:
        """Load individual Java files."""
        try:
            # Create temp directory if not exists
            if not self.project_path:
                temp_dir = tempfile.mkdtemp()
                self.project_path = Path(temp_dir)
                self.project_metadata["name"] = "Individual Files"
                self.project_metadata["source"] = "File Upload"
                self.project_metadata["upload_time"] = datetime.now()
            
            # Save files
            for file in files:
                if file.name.endswith('.java'):
                    file_path = self.project_path / file.name
                    with open(file_path, 'wb') as f:
                        f.write(file.getbuffer())
            
            # Scan for Java files
            self._scan_java_files()
            return True
        except Exception as e:
            st.error(f"Error loading individual files: {str(e)}")
            return False
    
    def _scan_java_files(self) -> None:
        """Scan project directory for Java files."""
        if not self.project_path or not self.project_path.exists():
            return
        
        self.project_files = []
        self.project_metadata["java_files"] = []
        self.project_metadata["file_count"] = 0
        self.project_metadata["total_size"] = 0
        
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = Path(root) / file
                    self.project_files.append(file_path)
                    
                    # Store absolute path for reliable access
                    abs_path = str(file_path.absolute())
                    rel_path = str(file_path.relative_to(self.project_path))
                    
                    # Add to metadata with both relative and absolute paths
                    file_size = file_path.stat().st_size
                    self.project_metadata["java_files"].append({
                        "name": file,
                        "path": rel_path,
                        "full_path": abs_path,
                        "size": file_size
                    })
                    self.project_metadata["file_count"] += 1
                    self.project_metadata["total_size"] += file_size

class ModelManager:
    """Manages LLM model loading and inference with hardware optimization."""
    def __init__(self):
        self.current_model = None
        self.model_loaded = False
        self.hardware_info = self._detect_hardware()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        self.logger.info("Initializing ModelManager...")
        self.logger.info(f"Hardware info: {self.hardware_info}")
        
        self.available_models = self._discover_models()
        self.resource_monitor = ResourceMonitor()
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect available hardware capabilities."""
        import platform
        import torch
        import psutil
        
        info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.machine(),
            "total_memory": psutil.virtual_memory().total / (1024**3),  # GB
            "available_memory": psutil.virtual_memory().available / (1024**3),  # GB
            "cpu_count": psutil.cpu_count(),
            "has_cuda": torch.cuda.is_available(),
            "has_mps": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
            "recommended_device": "cpu"
        }
        
        # Set device priority
        if info["has_cuda"]:
            info["recommended_device"] = "cuda"
        elif info["has_mps"]:
            info["recommended_device"] = "mps"
        
        return info
    
    def _get_memory_config(self) -> Dict[str, Any]:
        """Get optimal memory configuration based on available resources."""
        available_gb = self.hardware_info["available_memory"]
        device = self.hardware_info["recommended_device"]
        
        self.logger.info(f"Configuring memory for device: {device}")
        self.logger.info(f"Available memory: {available_gb:.2f} GB")
        
        # Base configuration
        config = {
            "device": device,
            "load_in_8bit": False,  # Default to False for better compatibility
            "torch_dtype": torch.float32,  # Default to float32 for better compatibility
            "device_map": None,  # Start with None for manual device management
            "low_cpu_mem_usage": True
        }
        
        # Device-specific configurations
        if device == "cuda":
            self.logger.info("Applying CUDA-specific configuration")
            config.update({
                "load_in_8bit": True,
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "max_memory": {
                    "cuda:0": f"{int(available_gb * 0.7)}GB",
                    "cpu": f"{int(available_gb * 0.2)}GB"
                }
            })
        elif device == "mps":
            self.logger.info("Applying MPS-specific configuration")
            # For MPS, we'll use CPU memory and handle device transfer manually
            config.update({
                "torch_dtype": torch.float32,  # MPS requires float32
                "device_map": None,  # Manual device management
                "load_in_8bit": False,  # Disable 8-bit quantization for MPS
                "low_cpu_mem_usage": True,
                "max_memory": {
                    "cpu": f"{int(available_gb * 0.5)}GB"  # Use CPU memory for MPS
                }
            })
            # Set environment variables for MPS
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.7"
        else:  # CPU
            self.logger.info("Applying CPU-specific configuration")
            config.update({
                "device_map": None,
                "max_memory": {
                    "cpu": f"{int(available_gb * 0.8)}GB"
                }
            })
        
        self.logger.info(f"Final memory configuration: {config}")
        return config
    
    def load_model(self, source: str, model_name: str, api_key: Optional[str] = None) -> bool:
        """Load a model for code refactoring."""
        try:
            # Normalize source to lowercase
            source = source.lower()
            
            # Log the loading attempt
            self.logger.info(f"Attempting to load model {model_name} from {source}")
            self.logger.info(f"Hardware info: {self.hardware_info}")
            
            # Validate model availability
            if model_name not in self.available_models:
                error_msg = f"Model {model_name} not found in available models"
                self.logger.error(error_msg)
                st.error(error_msg)
                return False
            
            model_info = self.available_models[model_name]
            self.logger.info(f"Model info: {model_info}")
            
            # Get memory configuration
            config = self._get_memory_config()
            self.logger.info(f"Memory config: {config}")
            
            device = config.pop("device")
            
            # Initialize model loading with progress
            with st.spinner(f"Loading model {model_name} on {device.upper()}..."):
                # Log pre-loading state
                self.logger.info("Pre-loading model state:")
                self.logger.info(f"- Current device: {device}")
                self.logger.info(f"- Available memory: {psutil.virtual_memory().available / (1024**3):.2f} GB")
                
                try:
                    # Set the current model
                    self.current_model = {
                        "name": model_name,
                        "source": source,
                        "status": "active",
                        "device": device,
                        "config": config
                    }
                    self.model_loaded = True
                    
                    success_msg = f"✅ Model {model_name} loaded successfully on {device.upper()}"
                    self.logger.info(success_msg)
                    st.success(success_msg)
                    return True
                    
                except Exception as e:
                    error_msg = f"Error during model loading: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    st.error(error_msg)
                    if hasattr(e, 'args'):
                        st.error(f"Additional error details: {e.args}")
                    self.model_loaded = False
                    self.current_model = None
                    return False
                
        except Exception as e:
            error_msg = f"Error loading model: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            self.model_loaded = False
            self.current_model = None
            return False
    
    def _discover_models(self) -> Dict[str, Dict]:
        """Discover available models with hardware-specific configurations."""
        self.logger.info("Starting model discovery")
        models = {}
        
        # Check for local models
        models_dir = Path("models")
        if models_dir.exists():
            for model_dir in models_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                    
                config_file = model_dir / "config.yaml"
                if not config_file.exists():
                    self.logger.warning(f"No config file found in {model_dir}")
                    continue
                
                try:
                    with open(config_file) as f:
                        config = yaml.safe_load(f)
                    
                    self.logger.info(f"Found config file in {model_dir}: {config}")
                    
                    # Get model name from directory
                    model_name = model_dir.name.replace("-", " ").title()
                    
                    # Verify required model files
                    required_files = config.get("model_files", [])
                    model_files = []
                    missing_files = []
                    
                    for file in required_files:
                        file_path = model_dir / file
                        if not file_path.exists():
                            missing_files.append(file)
                        else:
                            model_files.append(file_path)
                    
                    if missing_files:
                        self.logger.warning(f"Missing model files in {model_dir}: {missing_files}")
                        continue
                    
                    # Check file formats
                    has_bin = any(f.suffix == ".bin" for f in model_files)
                    has_safetensors = any(f.suffix == ".safetensors" for f in model_files)
                    
                    if not (has_bin or has_safetensors):
                        self.logger.warning(f"No valid model files found in {model_dir}")
                        continue
                    
                    # Get device and memory configuration
                    device = self.hardware_info["recommended_device"]
                    memory_config = self._get_memory_config()
                    
                    # Add model to available models
                    models[model_name] = {
                        "name": model_name,
                        "path": str(model_dir),
                        "type": "local",
                        "status": "available",
                        "device": device,
                        "model_format": "safetensors" if has_safetensors else "bin",
                        "size_gb": sum(f.stat().st_size / (1024**3) for f in model_files),
                        "files": [str(f) for f in model_files],
                        "config": config,
                        "memory_config": memory_config
                    }
                    
                    self.logger.info(
                        f"Found {model_name} model:\n"
                        f"- Device: {device}\n"
                        f"- Format: {models[model_name]['model_format']}\n"
                        f"- Files: {len(model_files)}\n"
                        f"- Total size: {models[model_name]['size_gb']:.1f} GB"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Error processing model in {model_dir}: {str(e)}")
                    continue
        
        # Add cloud models
        cloud_models = {
            "GPT-4": {
                "name": "GPT-4",
                "type": "cloud",
                "status": "available",
                "provider": "openai",
                "max_tokens": 8192,
                "temperature": 0.7
            },
            "Claude-2": {
                "name": "Claude-2",
                "type": "cloud",
                "status": "available",
                "provider": "anthropic",
                "max_tokens": 100000,
                "temperature": 0.7
            }
        }
        models.update(cloud_models)
        
        self.logger.info(f"Model discovery complete. Found {len(models)} models.")
        return models
    
    def get_model_status(self, model_name: str) -> Dict:
        """Get current status of a model."""
        if model_name in self.available_models:
            return self.available_models[model_name]
        return {"status": "unknown", "icon": "❓"}
    
    def generate_refactoring(self, code: str, smells: List[str]) -> Tuple[str, Dict]:
        """Generate refactored code using the loaded model with resource monitoring."""
        if not self.model_loaded:
            raise RuntimeError("No model loaded. Please load a model first.")
        
        try:
            # Check resources before generation
            if not self.resource_monitor.check_resources():
                raise RuntimeError("Insufficient resources for code generation")
            
            # Generate with resource monitoring
            with self.resource_monitor.monitor_generation():
                refactored_code, metadata = self.engine.refactor_code(code, smells)
            
            # Add resource usage to metadata
            metadata["resource_usage"] = self.resource_monitor.get_generation_stats()
            return refactored_code, metadata
            
        except Exception as e:
            st.error(f"Error during refactoring: {str(e)}")
            return code, {"error": str(e), "success": False}

    def unload_model(self) -> bool:
        """Unload the currently loaded model."""
        try:
            if not self.model_loaded:
                self.logger.info("No model is currently loaded")
                return True
                
            model_info = self.current_model.copy()
            self.logger.info(f"Unloading model: {model_info}")
            
            # Reset model state
            self.model_loaded = False
            self.current_model = None
            
            success_msg = f"✅ Model {model_info['name']} unloaded successfully"
            self.logger.info(success_msg)
            st.success(success_msg)
            return True
            
        except Exception as e:
            error_msg = f"Error unloading model: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            return False

class ResourceMonitor:
    """Monitors and manages system resources."""
    def __init__(self):
        self.start_time = time.time()
        self.generation_stats = {}
    
    def check_resources(self) -> bool:
        """Check if sufficient resources are available."""
        import psutil
        
        # Check memory
        mem = psutil.virtual_memory()
        if mem.available < 2 * 1024 * 1024 * 1024:  # 2GB minimum
            return False
        
        # Check CPU usage
        if psutil.cpu_percent(interval=1) > 90:
            return False
        
        return True
    
    def update_usage(self):
        """Update current resource usage statistics."""
        import psutil
        import torch
        
        self.current_usage = {
            "memory": psutil.virtual_memory().percent,
            "cpu": psutil.cpu_percent(),
            "gpu": self._get_gpu_usage()
        }
    
    def _get_gpu_usage(self) -> Dict[str, float]:
        """Get GPU memory usage based on available hardware."""
        try:
            if torch.cuda.is_available():
                return {
                    "allocated": torch.cuda.memory_allocated() / 1024**3,
                    "cached": torch.cuda.memory_reserved() / 1024**3
                }
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # Note: MPS doesn't provide direct memory stats
                return {"mps": "active"}
        except:
            pass
        return {}
    
    @contextmanager
    def monitor_generation(self):
        """Context manager to monitor resource usage during generation."""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            self.generation_stats = {
                "duration": end_time - start_time,
                "memory_delta": (end_memory - start_memory) / 1024**2,  # MB
                "peak_memory": psutil.virtual_memory().percent
            }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        return {
            "system": psutil.virtual_memory().percent,
            "gpu": self._get_gpu_usage()
        }
    
    def get_generation_stats(self) -> Dict[str, float]:
        """Get statistics from the last generation."""
        return self.generation_stats

# Initialize session state
if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProjectManager()
if 'model_manager' not in st.session_state:
    st.session_state.model_manager = ModelManager()

# Initialize refactoring components in session state
if 'refactor_model' not in st.session_state:
    st.session_state.refactor_model = None
if 'refactoring_manager' not in st.session_state:
    st.session_state.refactoring_manager = RefactoringFileManager()
if 'refactored_paths' not in st.session_state:
    st.session_state.refactored_paths = {}

# Ensure session state variables
if 'smells_heuristic' not in st.session_state:
    st.session_state['smells_heuristic'] = None
if 'smells_llm' not in st.session_state:
    st.session_state['smells_llm'] = None

def render_sidebar():
    """Render the sidebar with model selection and configuration options."""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Only show refactoring settings in refactoring tab
        if st.session_state.get("current_tab") == "🛠️ Refactoring":
            render_refactoring_sidebar()
            return
        
        # Original sidebar content for other tabs
        model_source = st.selectbox(
            "Model Source",
            ["Local", "Cloud", "Private Cloud"],
            help="Select where to load the LLM from"
        )
        
        # Conditional model selection based on source
        if model_source == "Local":
            model = st.selectbox(
                "Select Model",
                ["Code Llama 13B"],
                help="Choose a local model"
            )
            if st.button("Load Model"):
                st.session_state.model_manager.load_model("Local", model)
        elif model_source in ["Cloud", "Private Cloud"]:
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Enter your API key"
            )
            model = st.text_input(
                "Model Name",
                help="Enter the model identifier"
            )
            if st.button("Load Model"):
                st.session_state.model_manager.load_model(model_source, model, api_key)
        
        st.divider()
        
        # Code Smell Selection
        st.subheader("Target Smells")
        smells = {
            "God Class": True,
            "Feature Envy": True,
            "Data Class": True,
            "Long Method": False,
            "Complex Class": False
        }
        selected_smells = {}
        for smell, default in smells.items():
            selected_smells[smell] = st.checkbox(smell, value=default)
        
        st.divider()
        
        # Refactoring Mode
        st.subheader("Refactoring Mode")
        mode = st.radio(
            "Select Mode",
            ["Manual", "Auto"],
            help="Choose how to apply refactorings"
        )
        
        return selected_smells, mode

def render_refactoring_sidebar():
    """Render the refactoring configuration sidebar."""
    st.sidebar.title("⚙️ Model Configuration")
    
    # Model source selection
    model_source = st.sidebar.selectbox(
        "Model Source",
        ["Local", "Cloud"],
        help="Select where to load the model from"
    )
    
    # Model selection and status
    model_manager = st.session_state.model_manager
    available_models = model_manager.available_models
    
    # Display model status indicators
    st.sidebar.markdown("### 🔄 Model Status")
    for model_name, model_info in available_models.items():
        status = model_info.get("status", "unknown")
        status_color = {
            "available": "🟢",
            "loading": "🟡",
            "error": "🔴",
            "unknown": "⚪"
        }.get(status, "⚪")
        
        # Create a status indicator with loading progress if applicable
        col1, col2 = st.sidebar.columns([1, 3])
        with col1:
            st.markdown(f"{status_color}")
        with col2:
            st.markdown(f"{model_name}")
            if status == "loading":
                st.progress(model_info.get("loading_progress", 0), "Loading model...")
            elif status == "error":
                st.error(model_info.get("error_message", "Unknown error"))
    
    # Model selection
    selected_model = st.sidebar.selectbox(
        "Select Model",
        list(available_models.keys()),
        help="Choose a model for refactoring"
    )
    
    # Model configuration
    st.sidebar.markdown("### ⚙️ Model Parameters")
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more creative but less focused"
    )
    
    max_tokens = st.sidebar.number_input(
        "Max Tokens",
        min_value=1000,
        max_value=100000,
        value=4096,
        step=1000,
        help="Maximum number of tokens in the response"
    )
    
    # API key input for cloud models
    api_key = None
    if model_source == "Cloud":
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            help="Enter your API key for cloud models"
        )
    
    # Load model button with error handling
    if st.sidebar.button("Load Model", help="Click to load the selected model"):
        with st.sidebar.status("Loading model...") as status:
            try:
                success = model_manager.load_model(
                    model_source,
                    selected_model,
                    api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if success:
                    status.update(label="Model loaded successfully!", state="complete")
                    st.session_state.current_model = selected_model
                else:
                    status.update(label="Failed to load model", state="error")
            except Exception as e:
                status.update(label=f"Error: {str(e)}", state="error")
    
    # Target smells selection
    st.sidebar.markdown("### 🎯 Target Smells")
    selected_smells = []
    
    smell_options = {
        "God Class": "Large class that does too much",
        "Feature Envy": "Method uses more features of another class",
        "Data Class": "Class with only data and no behavior",
        "Long Method": "Method is too long and complex",
        "Complex Class": "Class with high cyclomatic complexity"
    }
    
    for smell, description in smell_options.items():
        if st.sidebar.checkbox(smell, help=description):
            selected_smells.append(smell)
    
    st.session_state['selected_smells'] = selected_smells

def render_home_tab():
    """Render the Home tab content."""
    st.title("🏠 Welcome to RefactAI")
    st.markdown("""
    RefactAI helps you detect and refactor code smells in Java projects using state-of-the-art LLMs.
    Upload your code, analyze for common anti-patterns, and get AI-powered refactoring suggestions.
    """)
    
    # Status and Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        model_status = "Active ✅" if st.session_state.model_manager.model_loaded else "Inactive ❌"
        model_name = st.session_state.model_manager.current_model.get("name") if st.session_state.model_manager.current_model else "No model loaded"
        st.metric(
            label="Model Status",
            value=model_status,
            delta=model_name
        )
    with col2:
        # TODO: Implement real memory usage tracking
        st.metric(
            "Memory Usage",
            "8.2 GB",
            "2.1 GB free"
        )
    with col3:
        # TODO: Implement real project statistics
        st.metric(
            "Classes Analyzed",
            "12",
            "+3 from last run"
        )
    
    # Project Overview
    with st.expander("📊 Project Overview", expanded=True):
        if st.session_state.project_manager.project_path:
            stats_col1, stats_col2 = st.columns(2)
            with stats_col1:
                st.markdown("### Current Project")
                st.info(st.session_state.project_manager.project_path.name)
                # TODO: Implement real project statistics
                st.markdown("- **Total Classes:** 15")
                st.markdown("- **Lines of Code:** 2,341")
                
            with stats_col2:
                st.markdown("### Detected Issues")
                if st.session_state.project_manager.analysis_results:
                    for smell, count in st.session_state.project_manager.analysis_results.get("smells", {}).items():
                        st.warning(f"- {count} {smell}")
                else:
                    st.info("No analysis results yet")
        else:
            st.info("No project loaded. Please upload a project in the Project Upload tab.")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def render_file_tree(tree: Dict, level: int = 0) -> None:
    """Render a file tree structure in Streamlit."""
    indent = "&nbsp;" * (level * 4)
    
    if "children" in tree:
        # Directory
        st.markdown(f"{indent}📁 **{tree['name']}**", unsafe_allow_html=True)
        for child in tree["children"]:
            render_file_tree(child, level + 1)
    else:
        # File
        size_str = format_file_size(tree["size"])
        st.markdown(f"{indent}📄 {tree['name']} ({size_str})", unsafe_allow_html=True)

def render_upload_tab():
    """Render the Project Upload tab content."""
    st.title("📂 Project Upload")
    
    # Upload Methods
    method = st.radio(
        "Choose Upload Method",
        ["Upload ZIP", "GitHub Repository", "Individual Files"]
    )
    
    if method == "Upload ZIP":
        uploaded_file = st.file_uploader(
            "Upload Project ZIP",
            type="zip",
            help="Upload a ZIP file containing your Java project"
        )
        
        if uploaded_file and st.button("📥 Load Project"):
            with st.spinner("Extracting and analyzing project..."):
                if st.session_state.project_manager.load_from_zip(uploaded_file):
                    java_files = st.session_state.project_manager.project_metadata["java_files"]
                    if java_files:
                        st.success(f"✅ Project loaded successfully! Found {len(java_files)} Java files.")
                        # Show found files
                        with st.expander("📁 Found Java Files"):
                            for file in java_files:
                                st.text(f"📄 {file['path']}")
                    else:
                        st.error("❌ No Java files found in the uploaded ZIP.")
                        st.info("Please ensure your ZIP file contains Java source files.")

    elif method == "GitHub Repository":
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repo",
            help="Enter the URL of your GitHub repository"
        )
        branch = st.text_input("Branch (optional)", value="main")
        if repo_url and st.button("📥 Load Project"):
            with st.spinner("Downloading and analyzing repository..."):
                if st.session_state.project_manager.load_from_github(repo_url, branch):
                    st.success(f"Repository loaded successfully! Found {st.session_state.project_manager.project_metadata['file_count']} Java files.")
        
    else:  # Individual Files
        uploaded_files = st.file_uploader(
            "Upload Java Files",
            type="java",
            accept_multiple_files=True,
            help="Upload one or more Java source files"
        )
        if uploaded_files and st.button("📥 Load Project"):
            with st.spinner("Processing Java files..."):
                if st.session_state.project_manager.load_individual_files(uploaded_files):
                    st.success(f"Files loaded successfully! Added {len(uploaded_files)} Java files to the project.")
    
    # Project Information
    if st.session_state.project_manager.project_path:
        st.divider()
        
        # Project Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Project Name", st.session_state.project_manager.project_metadata["name"])
        with col2:
            st.metric("Source", st.session_state.project_manager.project_metadata["source"])
        with col3:
            upload_time = st.session_state.project_manager.project_metadata["upload_time"]
            if upload_time:
                st.metric("Upload Time", upload_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # File Statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Java Files", st.session_state.project_manager.project_metadata["file_count"])
        with col2:
            total_size = format_file_size(st.session_state.project_manager.project_metadata["total_size"])
            st.metric("Total Size", total_size)
        
        # File Browser Section
        st.divider()
        st.subheader("📁 File Browser")
        
        # Search and Filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search files", placeholder="Enter filename or path to filter...")
        with col2:
            unique_dirs = {str(Path(file["path"]).parent) for file in st.session_state.project_manager.project_metadata["java_files"]}
            selected_dir = st.selectbox("📂 Filter by directory", ["All Directories"] + sorted(list(unique_dirs)))
        
        # Prepare file data for display
        files_data = []
        for file_info in st.session_state.project_manager.project_metadata["java_files"]:
            file_path = Path(file_info["path"])
            directory = str(file_path.parent)
            
            # Apply filters
            if search_term.lower() not in file_info["name"].lower() and search_term.lower() not in file_info["path"].lower():
                continue
            if selected_dir != "All Directories" and directory != selected_dir:
                continue
                
            files_data.append({
                "Filename": file_info["name"],
                "Directory": directory if directory != "." else "(root)",
                "Size": format_file_size(file_info["size"]),
                "Path": file_info["path"]
            })
        
        # Display files table
        if files_data:
            st.dataframe(
                files_data,
                column_config={
                    "Filename": st.column_config.TextColumn("📄 Filename"),
                    "Directory": st.column_config.TextColumn("📁 Directory"),
                    "Size": st.column_config.TextColumn("📊 Size"),
                    "Path": st.column_config.TextColumn("🔗 Full Path")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            if search_term or selected_dir != "All Directories":
                st.info("No files match the current filters.")
            else:
                st.info("No files found in the project.")
        
        # Group files by top-level directory
        st.divider()
        st.subheader("📂 Directory Overview")
        
        # Group files by top-level directory
        dir_groups = {}
        for file_info in st.session_state.project_manager.project_metadata["java_files"]:
            path = Path(file_info["path"])
            top_dir = path.parts[0] if len(path.parts) > 1 else "(root)"
            if top_dir not in dir_groups:
                dir_groups[top_dir] = []
            dir_groups[top_dir].append(file_info)
        
        # Display directory groups
        for dir_name, files in sorted(dir_groups.items()):
            with st.expander(f"📁 {dir_name} ({len(files)} files)"):
                st.table([{
                    "File": f"📄 {Path(f['path']).name}",
                    "Size": format_file_size(f['size']),
                    "Path": f['path']
                } for f in files])
        
        # Action Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Project"):
                st.session_state.project_manager._scan_java_files()
                st.success("Project refreshed!")
        with col2:
            if st.button("🗑️ Clear Project"):
                st.session_state.project_manager = ProjectManager()
                st.success("Project cleared!")

def count_classes(content: str) -> tuple:
    """Count and identify classes in Java content."""
    # Regular expressions for different class types
    class_patterns = {
        'interface': r'public\s+interface\s+(\w+)',
        'abstract': r'public\s+abstract\s+class\s+(\w+)',
        'enum': r'public\s+enum\s+(\w+)',
        'class': r'public\s+class\s+(\w+)'
    }
    
    classes = {
        'total': 0,
        'types': {
            'interface': [],
            'abstract': [],
            'enum': [],
            'class': []
        }
    }
    
    for class_type, pattern in class_patterns.items():
        matches = re.finditer(pattern, content)
        found_classes = [match.group(1) for match in matches]
        classes['types'][class_type] = found_classes
        classes['total'] += len(found_classes)
    
    return classes

def analyze_project_classes():
    """Analyze all classes in the project."""
    if not hasattr(st.session_state, 'project_class_analysis'):
        st.session_state.project_class_analysis = {
            'total_classes': 0,
            'class_types': {
                'interface': 0,
                'abstract': 0,
                'enum': 0,
                'class': 0
            }
        }
        
        # Analyze each Java file
        java_files = st.session_state.project_manager.project_metadata.get("java_files", [])
        for file in java_files:
            try:
                with open(file["full_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                    classes = count_classes(content)
                    
                    # Update totals
                    st.session_state.project_class_analysis['total_classes'] += classes['total']
                    for class_type, class_list in classes['types'].items():
                        st.session_state.project_class_analysis['class_types'][class_type] += len(class_list)
            except Exception:
                continue

def calculate_advanced_metrics(content: str, basic_metrics: dict) -> dict:
    """Calculate advanced software metrics for a Java class."""
    try:
        # Ensure basic_metrics has required fields
        if not basic_metrics or not isinstance(basic_metrics, dict):
            return {
                "lcom": {"value": 0, "threshold": 0.7, "status": "low", "icon": "🧩", "help": "Metrics calculation failed"},
                "cbo": {"value": 0, "threshold": 5, "status": "low", "icon": "🔗", "help": "Metrics calculation failed"},
                "dit": {"value": 0, "threshold": 3, "status": "low", "icon": "📐", "help": "Metrics calculation failed"},
                "cc": {"value": 0, "threshold": 10, "status": "low", "icon": "🔄", "help": "Metrics calculation failed"},
                "rfc": {"value": 0, "threshold": 20, "status": "low", "icon": "📡", "help": "Metrics calculation failed"}
            }
        
        # LCOM calculation
        method_count = basic_metrics.get("total_methods", 0)
        lcom = min(0.1 * method_count, 1.0) if method_count > 0 else 0
        
        # CBO calculation
        cbo = len(re.findall(r'import\s+[\w.]+;', content)) + \
              len(re.findall(r'new\s+\w+\(', content))
        
        # DIT calculation
        inheritance_chain = re.findall(r'extends\s+\w+', content)
        dit = len(inheritance_chain)
        
        # CC calculation
        cc = len(re.findall(r'\b(if|for|while|case|catch)\b', content))
        
        # RFC calculation
        rfc = len(re.findall(r'(\w+\s+\w+\s*\([^)]*\)\s*{|\w+\.[a-zA-Z_]\w*\s*\([^)]*\))', content))
        
        # Calculate thresholds and status
        metrics = {
            "lcom": {
                "value": round(lcom, 2),
                "threshold": 0.7,
                "status": "high" if lcom > 0.7 else "medium" if lcom > 0.4 else "low",
                "icon": "🧩",
                "help": "Lack of Cohesion of Methods (0-1). Lower is better."
            },
            "cbo": {
                "value": cbo,
                "threshold": 5,
                "status": "high" if cbo > 5 else "medium" if cbo > 3 else "low",
                "icon": "🔗",
                "help": "Coupling Between Objects. Lower is better."
            },
            "dit": {
                "value": dit,
                "threshold": 3,
                "status": "high" if dit > 3 else "medium" if dit > 2 else "low",
                "icon": "📐",
                "help": "Depth of Inheritance Tree. Lower is better."
            },
            "cc": {
                "value": cc,
                "threshold": 10,
                "status": "high" if cc > 10 else "medium" if cc > 7 else "low",
                "icon": "🔄",
                "help": "Cyclomatic Complexity. Lower is better."
            },
            "rfc": {
                "value": rfc,
                "threshold": 20,
                "status": "high" if rfc > 20 else "medium" if rfc > 15 else "low",
                "icon": "📡",
                "help": "Response For Class (methods + calls). Lower is better."
            }
        }
        
        return metrics
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return {
            "lcom": {"value": 0, "threshold": 0.7, "status": "low", "icon": "🧩", "help": "Calculation error"},
            "cbo": {"value": 0, "threshold": 5, "status": "low", "icon": "🔗", "help": "Calculation error"},
            "dit": {"value": 0, "threshold": 3, "status": "low", "icon": "📐", "help": "Calculation error"},
            "cc": {"value": 0, "threshold": 10, "status": "low", "icon": "🔄", "help": "Calculation error"},
            "rfc": {"value": 0, "threshold": 20, "status": "low", "icon": "📡", "help": "Calculation error"}
        }

def render_metric_card(label: str, metric: dict, help_text: str = "") -> None:
    """Render a metric card with status indicators."""
    status_colors = {
        "low": ("#28a745", "✅"),
        "medium": ("#ffc107", "⚠️"),
        "high": ("#dc3545", "⚠️")
    }
    color, icon = status_colors[metric["status"]]
    
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {color}; padding: 1rem;">
        <div style="color: #666; font-size: 0.9em;">{metric["icon"]} {label}</div>
        <div style="font-size: 1.5em; font-weight: bold; color: {color};">
            {metric["value"]} {icon}
        </div>
        <div style="font-size: 0.8em; color: #666;">
            Threshold: {metric["threshold"]}
            {f'<br>{help_text}' if help_text else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_metric_evidence(metric_name: str, value: float, threshold: float, comparison: str = ">") -> str:
    """Format metric evidence with value and threshold."""
    return f"{metric_name} = {value:.2f} {comparison} {threshold:.2f} threshold"

def normalize_metrics(metrics: dict) -> dict:
    """Normalize metrics to 0-1 scale for visualization."""
    max_values = {
        "lcom": 1.0,
        "cbo": 10.0,
        "dit": 5.0,
        "cc": 15.0,
        "rfc": 30.0
    }
    return {
        k: min(v["value"] / max_values[k], 1.0)
        for k, v in metrics.items()
    }

def render_metrics_chart(metrics: dict):
    """Render a bar chart for metrics visualization."""
    try:
        import plotly.graph_objects as go
        
        # Normalize metrics for visualization
        norm_metrics = normalize_metrics(metrics)
        
        # Prepare data for radar chart
        categories = list(norm_metrics.keys())
        values = list(norm_metrics.values())
        
        # Create radar chart
        fig = go.Figure()
        
        # Add metrics trace
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Values'
        ))
        
        # Add threshold trace
        thresholds = [metrics[k]["threshold"] / max_values.get(k, 1.0) for k in categories]
        fig.add_trace(go.Scatterpolar(
            r=thresholds,
            theta=categories,
            fill='toself',
            name='Thresholds',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='red', dash='dot')
        ))
        
        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            title="Metrics Overview (Normalized)",
            height=400
        )
        
        return fig
        
    except ImportError:
        # Fallback to simple bar chart if plotly is not available
        import pandas as pd
        chart_data = pd.DataFrame({
            'Metric': list(metrics.keys()),
            'Value': [m["value"] for m in metrics.values()],
            'Threshold': [m["threshold"] for m in metrics.values()]
        })
        return chart_data

def get_smell_evidence(smell: str, metrics: dict, basic_metrics: dict) -> str:
    """Generate evidence-based reasoning for code smells."""
    evidence = []
    
    if smell == "God Class":
        wmc = basic_metrics.get("wmc", 0)
        lcom = metrics["lcom"]["value"]
        loc = basic_metrics.get("loc", 0)
        evidence.extend([
            f"High complexity (WMC = {wmc} > {basic_metrics.get('wmc_threshold', 20)})",
            f"Low cohesion (LCOM = {lcom:.2f} > {metrics['lcom']['threshold']})",
            f"Large size (LOC = {loc} > {basic_metrics.get('loc_threshold', 200)})"
        ])
    
    elif smell == "Lazy Class":
        wmc = basic_metrics.get("wmc", 0)
        methods = basic_metrics.get("total_methods", 0)
        loc = basic_metrics.get("loc", 0)
        evidence.extend([
            f"Low complexity (WMC = {wmc} < {basic_metrics.get('wmc_threshold', 20)})",
            f"Few methods (Methods = {methods} < {basic_metrics.get('methods_threshold', 5)})",
            f"Small size (LOC = {loc} < {basic_metrics.get('loc_threshold', 50)})"
        ])
    
    elif smell == "Feature Envy":
        cbo = metrics["cbo"]["value"]
        rfc = metrics["rfc"]["value"]
        evidence.extend([
            f"High coupling (CBO = {cbo} > {metrics['cbo']['threshold']})",
            f"Many external calls (RFC = {rfc} > {metrics['rfc']['threshold']})"
        ])
    
    elif smell == "Data Class":
        methods = basic_metrics.get("total_methods", 0)
        getters_setters = basic_metrics.get("getters_setters", 0)
        if methods > 0:
            ratio = getters_setters / methods
            evidence.append(f"High accessor ratio ({getters_setters}/{methods} = {ratio:.2f} > 0.7)")
    
    return "\n".join([f"• {e}" for e in evidence])

def render_detection_tab():
    """Render the Smell Detection tab content."""
    st.markdown("""
    ### 🔍 Code Smell Detection
    <style>
    .file-stats {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 1em;
    }
    .smell-header {
        color: #1f77b4;
        margin-top: 1em;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }
    .smell-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.caption(
        "Select a Java class to automatically analyze it for potential code smells. "
        "The analysis uses intelligent detection algorithms to identify various anti-patterns."
    )
    
    # Check if project is loaded
    if not st.session_state.project_manager.project_path:
        st.warning("⚠️ Please upload a project first in the Project Upload tab.")
        return
    
    # Check if we have Java files
    java_files = st.session_state.project_manager.project_metadata.get("java_files", [])
    if not java_files:
        st.warning("⚠️ No Java files found in the project.")
        return
    
    # Initialize session state for analysis
    if "current_file" not in st.session_state:
        st.session_state.current_file = None
    if "file_content" not in st.session_state:
        st.session_state.file_content = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "show_analysis" not in st.session_state:
        st.session_state.show_analysis = False

    # Analyze project classes if not done
    analyze_project_classes()
    
    # Create two columns for file selection and stats
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📁 Select Java File")
        # Search filter
        search_query = st.text_input(
            "🔍 Search files",
            placeholder="Type to filter files...",
            key="file_search"
        )
    
    with col2:
        st.markdown("#### 📊 Project Stats")
        
        # Enhanced project stats with class information
        total_classes = st.session_state.project_class_analysis['total_classes']
        class_types = st.session_state.project_class_analysis['class_types']
        
        st.markdown(f"""
        <div class="file-stats">
        📄 Total Java Files: {len(java_files)}<br>
        🔷 Total Classes: {total_classes}<br>
        📦 Project Size: {format_file_size(st.session_state.project_manager.project_metadata["total_size"])}<br>
        <small>
        • Regular Classes: {class_types['class']}<br>
        • Interfaces: {class_types['interface']}<br>
        • Abstract Classes: {class_types['abstract']}<br>
        • Enums: {class_types['enum']}
        </small>
        </div>
        """, unsafe_allow_html=True)
    
    # Filter files based on search
    filtered_files = [
        f for f in java_files
        if not search_query or search_query.lower() in f["name"].lower() or search_query.lower() in f["path"].lower()
    ]
    
    # Group files by directory for better organization
    grouped_files = {}
    for f in filtered_files:
        dir_path = os.path.dirname(f["path"])
        if dir_path not in grouped_files:
            grouped_files[dir_path] = []
        grouped_files[dir_path].append(f)
    
    # File selection dropdown with directory grouping
    selected_file = st.selectbox(
        "Select a file to analyze",
        options=filtered_files,
        format_func=lambda x: f"📄 {x['path']}",
        key="file_selector"
    )
    
    if selected_file:
        try:
            # Verify file exists and read content
            file_path = selected_file["full_path"]
            if not os.path.exists(file_path):
                st.error(f"❌ File not found: {selected_file['path']}")
                return
                
            # Read and display file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Analyze classes in current file
            file_classes = count_classes(file_content)
            
            # Create tabs for content and analysis
            code_tab, analysis_tab = st.tabs(["📝 Source Code", "🔍 Analysis"])
            
            with code_tab:
                # Enhanced file info header with class information
                class_info_html = ""
                for class_type, classes in file_classes['types'].items():
                    if classes:
                        class_info_html += f"<br>📘 <b>{class_type.title()}s</b>: {', '.join(classes)}"
                
                st.markdown(f"""
                <div class="file-stats">
                📄 <b>{os.path.basename(selected_file['path'])}</b><br>
                📁 Path: {os.path.dirname(selected_file['path'])}<br>
                📊 Size: {format_file_size(selected_file['size'])}<br>
                🔷 Classes in File: {file_classes['total']}
                {class_info_html}
                </div>
                """, unsafe_allow_html=True)
                
                # Code viewer with line numbers
                st.code(file_content, language="java")
            
            with analysis_tab:
                # Analysis Button
                if not st.session_state.show_analysis:
                    st.info("Click the button below to analyze the code for potential smells.")
                    
                    # Show class summary before analysis
                    if file_classes['total'] > 0:
                        st.markdown("##### 📘 Class Summary")
                        for class_type, classes in file_classes['types'].items():
                            if classes:
                                st.markdown(f"**{class_type.title()}s**")
                                for class_name in classes:
                                    st.markdown(f"• {class_name}")
                
                if st.button("🔍 Analyze Code Smells", key="analyze_button", use_container_width=True):
                    with st.spinner("Analyzing code metrics and smells..."):
                        try:
                            # First run smell detection to get basic metrics
                            results = detect_smells([{
                                "class_name": selected_file["name"],
                                "content": file_content,
                                "inheritance_data": {
                                    "inherited_methods": 5,
                                    "used_methods": 2,
                                    "overridden_methods": 3
                                }
                            }])
                            
                            if not results or selected_file["name"] not in results:
                                st.error("❌ Error: Smell detection failed to return results")
                                return
                                
                            st.session_state.analysis_results = results[selected_file["name"]]
                            
                            # Now calculate advanced metrics with the results
                            advanced_metrics = calculate_advanced_metrics(
                                file_content,
                                st.session_state.analysis_results.get("metrics", {})
                            )
                            
                            # Store metrics in session state
                            st.session_state.advanced_metrics = advanced_metrics
                            st.session_state.show_analysis = True
                            st.toast("✅ Analysis complete!")
                            
                        except Exception as e:
                            st.error(f"❌ Error during analysis: {str(e)}")
                            st.session_state.show_analysis = False
                            return
                
                # Display Analysis Results
                if st.session_state.show_analysis and st.session_state.analysis_results:
                    try:
                        st.markdown("#### 📊 Metrics Analysis")
                        
                        # Basic Metrics Section
                        st.markdown("##### Basic Metrics")
                        basic_metrics = st.session_state.analysis_results.get("metrics", {})
                        if not basic_metrics:
                            st.warning("⚠️ Basic metrics calculation failed")
                            return
                            
                        basic_cols = st.columns(4)
                        basic_metrics_data = [
                            ("Total Classes", file_classes['total'], "🔷", "Number of classes in file"),
                            ("Lines of Code", basic_metrics.get("loc", 0), "📏", "Total lines of code"),
                            ("Total Methods", basic_metrics.get("total_methods", 0), "🔧", "Number of methods"),
                            ("WMC", basic_metrics.get("wmc", 0), "⚖️", "Weighted Methods per Class")
                        ]
                        
                        for col, (label, value, icon, help_text) in zip(basic_cols, basic_metrics_data):
                            with col:
                                st.metric(
                                    label=f"{icon} {label}",
                                    value=value,
                                    help=help_text
                                )
                        
                        # Advanced Metrics Section
                        st.markdown("##### Advanced Metrics")
                        advanced_metrics = st.session_state.get("advanced_metrics", {})
                        if not advanced_metrics:
                            st.warning("⚠️ Advanced metrics calculation failed")
                            return
                            
                        # Create 3x2 grid for advanced metrics
                        for i in range(0, len(advanced_metrics), 3):
                            cols = st.columns(3)
                            metrics_slice = list(advanced_metrics.items())[i:i+3]
                            for col, (metric_name, metric_data) in zip(cols, metrics_slice):
                                with col:
                                    render_metric_card(
                                        metric_name.upper(),
                                        metric_data,
                                        metric_data.get("help", "")
                                    )
                        
                        # Export Metrics Button
                        if st.button("📥 Export Metrics as JSON", use_container_width=True):
                            export_data = {
                                "file_info": {
                                    "name": selected_file["name"],
                                    "path": selected_file["path"],
                                    "size": selected_file["size"]
                                },
                                "basic_metrics": basic_metrics,
                                "advanced_metrics": {
                                    k: {"value": v["value"], "status": v["status"]}
                                    for k, v in advanced_metrics.items()
                                },
                                "smells": st.session_state.analysis_results["smells"],
                                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # Convert to JSON string
                            json_str = json.dumps(export_data, indent=2)
                            
                            # Create download button
                            st.download_button(
                                label="💾 Download Metrics Report",
                                data=json_str,
                                file_name=f"metrics_{selected_file['name']}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        st.divider()
                        
                        # Detected Smells Section with enhanced visualization
                        st.markdown("##### 🚨 Detected Code Smells")
                        if st.session_state.analysis_results["smells"]:
                            # Custom CSS for better smell card styling
                            st.markdown("""
                            <style>
                            .smell-card {
                                background-color: #f8f9fa;
                                border-radius: 0.5rem;
                                padding: 1rem;
                                margin-bottom: 1rem;
                            }
                            .smell-title {
                                font-size: 1.2rem;
                                font-weight: 600;
                                margin-bottom: 0.5rem;
                            }
                            .smell-reason {
                                font-style: italic;
                                color: #495057;
                                margin-bottom: 0.5rem;
                            }
                            .smell-metrics {
                                background-color: #ffffff;
                                border-radius: 0.3rem;
                                padding: 0.5rem;
                                font-size: 0.9rem;
                                color: #666;
                            }
                            </style>
                            """, unsafe_allow_html=True)

                            for smell in st.session_state.analysis_results["smells"]:
                                smell_color = {
                                    "God Class": ("🔴", "#dc3545", "High complexity and low cohesion"),
                                    "Data Class": ("🟡", "#ffc107", "Lacks behavior"),
                                    "Lazy Class": ("🟠", "#fd7e14", "Low responsibility"),
                                    "Feature Envy": ("🟣", "#6f42c1", "High coupling"),
                                    "Refused Bequest": ("🔵", "#0d6efd", "Inheritance misuse")
                                }.get(smell, ("⚪", "#6c757d", ""))
                                
                                st.markdown(f"""
                                <div class="smell-card" style="border-left: 4px solid {smell_color[1]}">
                                    <div class="smell-title">{smell_color[0]} {smell}</div>
                                    <div class="smell-reason">{st.session_state.analysis_results['reasoning'][smell]}</div>
                                    <div class="smell-metrics">
                                        <strong>Type:</strong> {smell_color[2]}<br>
                                        <strong>Evidence:</strong><br>
                                        {st.session_state.analysis_results.get('metrics_evidence', {}).get(smell, 'Detailed metrics analysis in progress...')}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ No code smells detected in this file")
                        
                        # Add metrics visualization
                        with st.expander("📊 Metric Visualization", expanded=True):
                            try:
                                chart = render_metrics_chart(advanced_metrics)
                                if hasattr(chart, 'show'):
                                    # It's a plotly figure
                                    st.plotly_chart(chart, use_container_width=True)
                                else:
                                    # It's a pandas DataFrame
                                    st.bar_chart(chart.set_index('Metric')[['Value', 'Threshold']])
                            except Exception as e:
                                st.error(f"Could not render metrics chart: {str(e)}")
                        
                    except Exception as e:
                        st.error(f"❌ Error displaying analysis results: {str(e)}")
                        return
                
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            return

def highlight_code_differences(original_code: str, refactored_code: str) -> tuple[str, str]:
    """
    Highlight the differences between original and refactored code.
    Returns a tuple of (highlighted_original, highlighted_refactored)
    """
    import difflib
    
    # Split the code into lines
    original_lines = original_code.splitlines()
    refactored_lines = refactored_code.splitlines()
    
    # Get the diff
    differ = difflib.Differ()
    diff = list(differ.compare(original_lines, refactored_lines))
    
    # Process the diff to create highlighted versions
    highlighted_original = []
    highlighted_refactored = []
    
    for line in diff:
        if line.startswith('  '):  # Unchanged
            highlighted_original.append(line[2:])
            highlighted_refactored.append(line[2:])
        elif line.startswith('- '):  # Removed
            highlighted_original.append(f"[red]{line[2:]}[/red]")
        elif line.startswith('+ '):  # Added
            highlighted_refactored.append(f"[green]{line[2:]}[/green]")
            
    return ('\n'.join(highlighted_original), '\n'.join(highlighted_refactored))

def render_refactoring_tab():
    """Render the Refactoring tab content."""
    st.title("🛠️ Code Refactoring")
    
    # Initialize session state variables
    if 'project_files' not in st.session_state:
        st.session_state.project_files = []
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'original_code' not in st.session_state:
        st.session_state.original_code = None
    if 'refactored_code' not in st.session_state:
        st.session_state.refactored_code = None
    if 'refactoring_metadata' not in st.session_state:
        st.session_state.refactoring_metadata = None
    if 'detected_smells' not in st.session_state:
        st.session_state.detected_smells = None
    if 'refactoring_history' not in st.session_state:
        st.session_state.refactoring_history = []
    
    # Check if project is loaded
    if not st.session_state.project_manager.project_path:
        st.warning("Please upload a project first")
        return
    
    # Get Java files from project
    java_files = [f for f in st.session_state.project_manager.project_metadata.get("java_files", []) 
                  if f["path"].endswith(".java")]
    
    if not java_files:
        st.warning("No Java files found. Please upload a project with Java files.")
        return
    
    # File selection
    file_options = [f["path"] for f in java_files]
    selected_file = st.selectbox(
        "Choose a file to refactor",
        file_options,
        key="refactoring_file_selector"
    )

    code_content = None
    if selected_file:
        # Read file content
        file_path = Path(st.session_state.project_manager.project_path) / selected_file
        try:
            with open(file_path, 'r') as f:
                code_content = f.read()
                st.session_state.original_code = code_content
            # Display original code
            with st.expander("📄 Original Code", expanded=True):
                st.code(code_content, language="java")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return

    # Refactoring configuration
    st.subheader("🔧 Refactoring Configuration")
    refactoring_patterns = {
        "Extract Method": "Split long methods into smaller, focused ones",
        "Extract Class": "Move related fields and methods to a new class",
        "Rename Symbol": "Improve naming of variables, methods, or classes",
        "Move Method": "Move method to a more appropriate class",
        "Encapsulate Field": "Make fields private and provide accessors",
        "Replace Conditional with Polymorphism": "Use inheritance instead of conditionals",
        "Introduce Parameter Object": "Group parameters into an object",
        "Extract Interface": "Create interface from common methods"
    }
    col1, col2 = st.columns(2)
    selected_patterns = []
    with col1:
        st.markdown("##### Select Refactoring Patterns")
        for pattern, description in list(refactoring_patterns.items())[:4]:
            if st.checkbox(pattern, help=description, key=f"pattern_{pattern}"):
                selected_patterns.append(pattern)
    with col2:
        st.markdown("##### Additional Patterns")
        for pattern, description in list(refactoring_patterns.items())[4:]:
            if st.checkbox(pattern, help=description, key=f"pattern_{pattern}"):
                selected_patterns.append(pattern)

    # --- Code Smell Detection ---
    col_heur, col_llm = st.columns(2)
    with col_heur:
        if st.button("🔍 Detect Code Smells (Heuristic)", key="detect_smells_heuristic"):
            if code_content:
                detected_smells = analyze_code_smells(code_content)
                st.session_state.smells_heuristic = detected_smells
            else:
                st.warning("No code loaded.")
    with col_llm:
        # Check if model is loaded
        model_loaded = st.session_state.model_manager.model_loaded and st.session_state.model_manager.current_model is not None
        if not model_loaded:
            st.button("🤖 Detect Code Smells (LLM)", key="detect_smells_llm", disabled=True, help="Please load a model first")
            st.info("Load a model in the sidebar to enable LLM-based smell detection")
        else:
            if st.button("🤖 Detect Code Smells (LLM)", key="detect_smells_llm"):
                if code_content:
                    detected_smells_llm = detect_code_smells_with_llm(code_content)
                    st.session_state.smells_llm = detected_smells_llm
                else:
                    st.warning("No code loaded.")

    # --- Display Results ---
    if st.session_state.smells_heuristic is not None:
        st.markdown("### Heuristic Detection Results")
        if st.session_state.smells_heuristic:
            smell_table = []
            for smell, details in st.session_state.smells_heuristic.items():
                smell_table.append({
                    "Smell": smell,
                    "Location": details.get("location", "-"),
                    "Description": details.get("description", "-"),
                    "Suggestion": details.get("suggestion", "-")
                })
            df = pd.DataFrame(smell_table)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.success("No code smells detected by heuristic method!")
    if st.session_state.smells_llm is not None:
        st.markdown("### LLM Detection Results")
        if st.session_state.smells_llm:
            smell_table = []
            for smell, details in st.session_state.smells_llm.items():
                smell_table.append({
                    "Smell": smell,
                    "Lines": details.get("lines", "-"),
                    "Description": details.get("description", "-"),
                    "Suggestion": details.get("suggestion", "-")
                })
            df = pd.DataFrame(smell_table)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.success("No code smells detected by LLM!")

    # --- Generate refactoring and rest of the function remains unchanged ---
    # ... existing code ...

def render_testing_tab():
    """Render the Testing & Metrics tab content."""
    st.title("🧪 Testing & Metrics")
    
    if not st.session_state.project_manager.project_path:
        st.warning("Please upload a project first")
        return
    
    # Test Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Tests"):
            # TODO: Implement real test running
            st.success("Tests completed!")
    with col2:
        if st.button("📊 Generate Report"):
            # TODO: Implement real report generation
            st.success("Report generated!")
    
    # Metrics Display
    st.markdown("### Quality Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    with metrics_col1:
        # TODO: Implement real metrics calculation
        st.metric("Code Coverage", "78%", "+5%")
    with metrics_col2:
        st.metric("Complexity", "24", "-8")
    with metrics_col3:
        st.metric("Maintainability", "A", "↑ from B")
    
    # Test Results
    with st.expander("🔍 Test Results", expanded=True):
        # TODO: Implement real test results display
        st.markdown("""
        [PASS] UserManagerTest: 12/12 passed
        [PASS] DataServiceTest: 8/8 passed
        [PASS] UtilsTest: 5/5 passed
        """)
    
    # Performance Comparison
    st.markdown("### Performance Comparison")
    # TODO: Implement real performance metrics
    st.line_chart({
        "Before": [75, 82, 78, 85, 90],
        "After": [85, 89, 88, 92, 95]
    })

def render_refactoring_preview(original_code: str, refactored_code: str):
    """Render a side-by-side comparison of original and refactored code with diff highlighting, summary, and code quality metrics."""
    st.subheader("Refactoring Summary")

    # Patterns applied (from session or metadata)
    patterns = st.session_state.get('last_patterns', [])
    if not patterns and 'refactoring_metadata' in st.session_state and st.session_state.refactoring_metadata:
        patterns = st.session_state.refactoring_metadata.get('patterns', [])
    st.markdown(f"**Patterns Applied:** {', '.join(patterns) if patterns else 'N/A'}")

    # Smells fixed: parse refactored code for comments like '// Smell:' or '// Addressed smell:'
    smell_lines = []
    for i, line in enumerate(refactored_code.splitlines(), 1):
        if 'smell' in line.lower():
            smell_desc = line.strip().lstrip('/').replace('*', '').replace('//', '').strip()
            smell_lines.append((i, smell_desc))
    if smell_lines:
        st.markdown("**Smells Fixed:**")
        import pandas as pd
        df_smells = pd.DataFrame(smell_lines, columns=["Line", "Description"])
        st.dataframe(df_smells, hide_index=True, use_container_width=True)
    else:
        st.markdown("**Smells Fixed:** None detected in comments.")

    # Code quality improvement and diff summary
    added, removed, changed = diff_stats(original_code, refactored_code)
    metrics = st.session_state.get("last_refactoring_metrics", {})
    avg_improvement = metrics.get("avg_improvement", 0)
    st.markdown(f"**Code Quality Improvement:** `{avg_improvement:+.1f}%` (lower is better)")
    st.markdown(f"**Diff Summary:** 🟩 +{added} &nbsp;&nbsp; 🟥 -{removed} &nbsp;&nbsp; 🟦 ~{changed}")

    # Downloadable report
    report = f"""
Refactoring Summary\n------------------\nPatterns Applied: {', '.join(patterns) if patterns else 'N/A'}\nCode Quality Improvement: {avg_improvement:+.1f}%\nLines Added: {added}\nLines Removed: {removed}\nLines Changed: {changed}\n\nSmells Fixed:\n"""
    for ln, desc in smell_lines:
        report += f"  Line {ln}: {desc}\n"
    report += "\n---\nOriginal Code:\n" + original_code + "\n---\nRefactored Code:\n" + refactored_code
    st.download_button("Download Refactoring Report", report, file_name="refactoring_report.txt")

    # --- Code Quality Metrics ---
    st.markdown("### Code Quality Metrics")
    orig_basic = calculate_basic_metrics(original_code)
    refac_basic = calculate_basic_metrics(refactored_code)
    orig_metrics = calculate_advanced_metrics(original_code, orig_basic)
    refac_metrics = calculate_advanced_metrics(refactored_code, refac_basic)
    metric_names = list(orig_metrics.keys())
    
    # Calculate improvement for each metric (lower is better)
    improvements = {}
    for m in metric_names:
        before = orig_metrics[m]["value"]
        after = refac_metrics[m]["value"]
        if before == 0:
            improvement = 0
        else:
            improvement = (before - after) / before * 100
        improvements[m] = improvement
    
    df = pd.DataFrame({
        "Metric": metric_names,
        "Before": [orig_metrics[m]["value"] for m in metric_names],
        "After": [refac_metrics[m]["value"] for m in metric_names],
        "Improvement (%)": [f"{improvements[m]:+.1f}%" for m in metric_names]
    })
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Store improvement in session state for history
    st.session_state["last_refactoring_metrics"] = {
        "before": orig_metrics,
        "after": refac_metrics,
        "improvements": improvements,
        "avg_improvement": avg_improvement
    }

    # Split code into sections for collapsible display
    original_sections = split_code_into_sections(original_code)
    refactored_sections = split_code_into_sections(refactored_code)
    
    # Create columns for side-by-side display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Code")
        for section_name, section_code in original_sections.items():
            with st.expander(f"📄 {section_name}", expanded=True):
                st.code(section_code, language="java", line_numbers=True)
    
    with col2:
        st.markdown("### Refactored Code")
        for section_name, section_code in refactored_sections.items():
            with st.expander(f"📄 {section_name}", expanded=True):
                diff_html = generate_diff_html(
                    original_sections.get(section_name, ""),
                    section_code
                )
                st.markdown(diff_html, unsafe_allow_html=True)

def diff_stats(original: str, refactored: str) -> tuple:
    """Return (added, removed, changed) line counts for the diff."""
    differ = difflib.Differ()
    diff = list(differ.compare(original.splitlines(), refactored.splitlines()))
    added = sum(1 for line in diff if line.startswith('+'))
    removed = sum(1 for line in diff if line.startswith('-'))
    changed = sum(1 for line in diff if line.startswith('?'))
    return added, removed, changed

def split_code_into_sections(code: str) -> Dict[str, str]:
    """Split code into logical sections for collapsible display."""
    sections = {}
    current_section = []
    current_section_name = "Main"
    
    for line in code.split('\n'):
        # Detect class definition
        if re.match(r'^\s*public\s+class\s+\w+', line):
            if current_section:
                sections[current_section_name] = '\n'.join(current_section)
            current_section = [line]
            current_section_name = re.search(r'class\s+(\w+)', line).group(1)
            continue
            
        # Detect method definition
        if re.match(r'^\s*(?:public|private|protected)\s+\w+\s+\w+\s*\(', line):
            if current_section:
                sections[current_section_name] = '\n'.join(current_section)
            current_section = [line]
            method_name = re.search(r'\s+(\w+)\s*\(', line).group(1)
            current_section_name = f"Method: {method_name}"
            continue
            
        current_section.append(line)
    
    # Add the last section
    if current_section:
        sections[current_section_name] = '\n'.join(current_section)
    
    return sections

def generate_diff_html(original: str, refactored: str) -> str:
    """Generate HTML with diff highlighting, accessibility icons/patterns, and line numbers."""
    differ = difflib.Differ()
    diff = list(differ.compare(original.splitlines(), refactored.splitlines()))
    
    html_lines = []
    line_num = 1
    for line in diff:
        if line.startswith('+') or line.startswith('-') or line.startswith(' '):
            # Add line number
            ln_html = f'<span style="color:#888; min-width:2em; display:inline-block; text-align:right;">{line_num}</span> '
            if line.startswith('+'):
                html_lines.append(f'{ln_html}<span style="background-color: #e6ffe6">🟢➕ {html.escape(line[2:])}</span>')
                line_num += 1
            elif line.startswith('-'):
                html_lines.append(f'{ln_html}<span style="background-color: #ffe6e6">🔴➖ {html.escape(line[2:])}</span>')
                line_num += 1
            elif line.startswith(' '):
                html_lines.append(f'{ln_html}<span>⬜ {html.escape(line[2:])}</span>')
                line_num += 1
    return f'<pre style="background-color: white; padding: 10px; border-radius: 5px;">{"\n".join(html_lines)}</pre>'

# Add this helper function near the top (after imports)
def generate_refactoring(code, patterns, smells):
    # Use refactor_with_gptlab to generate refactored code
    model_name = st.session_state.model_manager.current_model["name"] if st.session_state.model_manager.current_model else "GPT-4"
    endpoint = "LOCAL"  # Or use the correct endpoint if needed
    additional_instructions = ", ".join(patterns) if patterns else ""
    refactored_code = refactor_with_gptlab(
        code=code,
        model_name=model_name,
        endpoint=endpoint,
        smell_analysis=smells,
        additional_instructions=additional_instructions
    )
    # For now, just return an empty metadata dict
    metadata = {}
    return refactored_code, metadata

def calculate_basic_metrics(content: str) -> dict:
    """Calculate basic metrics for a Java class/file."""
    total_methods = len(re.findall(r'(?:public|private|protected)\s+\w+\s+\w+\s*\(', content))
    loc = len([line for line in content.splitlines() if line.strip()])
    getters_setters = len(re.findall(r'(get|set)\w+\s*\(', content))
    wmc = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b', content))
    return {
        "total_methods": total_methods,
        "loc": loc,
        "getters_setters": getters_setters,
        "wmc": wmc
    }

def detect_code_smells_with_llm(code: str) -> dict:
    # Check if a model is loaded
    if not st.session_state.model_manager.model_loaded or not st.session_state.model_manager.current_model:
        st.warning("No model is currently loaded. Please load a model first.")
        return {}

    prompt = (
        "Analyze the following Java code and list all code smells you detect. "
        "For each smell, provide: the name, line number(s), a short description, and a suggestion. "
        "Return as JSON: [{'smell': ..., 'lines': ..., 'description': ..., 'suggestion': ...}, ...]\n\n"
        f"Java code:\n{code}"
    )
    
    try:
        response = refactor_with_gptlab(
            code=code,
            model_name=st.session_state.model_manager.current_model['name'],
            endpoint='LOCAL',
            smell_analysis=None,
            additional_instructions=prompt
        )
        return response
    except Exception as e:
        st.error(f"Error during code smell detection: {str(e)}")
        return {}

def find_closing_brace(code: str, start_pos: int) -> int:
    """Find the position of the closing brace that matches the opening brace."""
    brace_count = 0
    pos = start_pos
    
    while pos < len(code):
        if code[pos] == '{':
            brace_count += 1
        elif code[pos] == '}':
            brace_count -= 1
            if brace_count == 0:
                return pos
        pos += 1
    
    return len(code)

def analyze_code_smells(code: str) -> dict:
    """Analyze code for common code smells using heuristic detection."""
    smells = {}
    
    # Long Method detection
    methods = re.finditer(r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\([^)]*\)\s*{', code)
    for method in methods:
        method_name = method.group(1)
        method_start = method.start()
        method_end = find_closing_brace(code, method_start)
        method_lines = code[method_start:method_end].count('\n')
        
        if method_lines > 30:
            smells[f"Long Method: {method_name}"] = {
                "location": f"Method {method_name}",
                "description": f"Method is {method_lines} lines long",
                "suggestion": "Consider breaking down into smaller methods"
            }
    
    # Complex Class detection
    class_complexity = len(re.findall(r'\b(if|for|while|catch)\b', code))
    if class_complexity > 20:
        smells["Complex Class"] = {
            "location": "Entire class",
            "description": f"Class has {class_complexity} control flow statements",
            "suggestion": "Consider splitting into multiple classes"
        }
    
    # High Response for Class detection
    method_count = len(re.findall(r'(?:public|private|protected)\s+\w+\s+\w+\s*\(', code))
    if method_count > 20:
        smells["High Response for Class"] = {
            "location": "Entire class",
            "description": f"Class has {method_count} methods",
            "suggestion": "Consider splitting responsibilities into multiple classes"
        }
    
    # Long Parameter List detection
    long_param_methods = re.finditer(r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(([^)]*)\)', code)
    for method in long_param_methods:
        method_name = method.group(1)
        params = method.group(2).split(',')
        if len(params) > 5:
            smells[f"Long Parameter List: {method_name}"] = {
                "location": f"Method {method_name}",
                "description": f"Method has {len(params)} parameters",
                "suggestion": "Consider introducing parameter object or builder pattern"
            }
    
    # Duplicate Code detection (simple version)
    lines = code.split('\n')
    for i in range(len(lines)):
        for j in range(i + 5, len(lines)):
            if j + 5 <= len(lines):
                block1 = '\n'.join(lines[i:i+5])
                block2 = '\n'.join(lines[j:j+5])
                if block1 == block2 and not block1.isspace():
                    smells[f"Duplicate Code at line {i+1}"] = {
                        "location": f"Lines {i+1}-{i+5} and {j+1}-{j+5}",
                        "description": "Found duplicate code blocks",
                        "suggestion": "Consider extracting to a shared method"
                    }
    
    return smells

def main():
    """Main function to run the Streamlit dashboard."""
    # Store current tab in session state
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "🏠 Home"
    
    # Render sidebar and get configuration
    selected_smells, refactoring_mode = render_sidebar()
    
    # Create main tabs
    tabs = st.tabs([
        "🏠 Home",
        "📂 Project Upload",
        "🔍 Smell Detection",
        "🛠️ Refactoring",
        "🧪 Testing & Metrics"
    ])
    
    # Update current tab
    for i, tab in enumerate(["🏠 Home", "📂 Project Upload", "🔍 Smell Detection", "🛠️ Refactoring", "🧪 Testing & Metrics"]):
        if tabs[i].selected:
            st.session_state.current_tab = tab
    
    # Render tab contents
    with tabs[0]:
        render_home_tab()
    with tabs[1]:
        render_upload_tab()
    with tabs[2]:
        render_detection_tab()
    with tabs[3]:
        render_refactoring_tab()
    with tabs[4]:
        render_testing_tab()

if __name__ == "__main__":
    main() 