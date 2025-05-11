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
from refactoring.file_utils import RefactoringFileManager
import difflib
import html
import pandas as pd
from gptlab_test import gptlab_chat, MODEL_OPTIONS  # Import what we need from gptlab_test
from refactoring.engine import RefactoringEngine
from gptlab_integration import refactor_with_gptlab, render_refactoring_preview
# --- Metrics utilities ---
from metrics_utils import calculate_advanced_metrics, normalize_metrics, calculate_health_score
from visualization_utils import render_metrics_chart

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

# TODO: Import your Java project analysis modules
# from java_analyzer import JavaProjectAnalyzer
# from smell_detector import SmellDetector
# from refactoring_engine import RefactoringEngine
# from test_runner import TestRunner
# from metrics_calculator import MetricsCalculator

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
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cpu"
        self.memory_config = {}
        self.logger = logging.getLogger(__name__)
        self.resource_monitor = ResourceMonitor()
        self.engine = RefactoringEngine()
        self.model_loaded = False
        self.current_model = None
    
    def load_model(self, model_name: str, source: str = "LOCAL", api_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Load a model from the specified source."""
        try:
            self.logger.info(f"Loading model {model_name} from {source}")
            
            # Check if model is already loaded
            if self.model_loaded and self.current_model and self.current_model["name"] == model_name:
                self.logger.info("Model already loaded")
                return True, None
            
            # Check resources before loading
            if not self.resource_monitor.check_resources():
                error_msg = "Insufficient resources for model loading"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Load model with resource monitoring
            with self.resource_monitor.monitor_loading():
                success, error = self.engine.load_model(
                    source=source,
                    model_name=model_name,
                    api_key=api_key,
                    device=self.device,
                    **self.memory_config
                )
            
            if success:
                self.model_loaded = True
                self.current_model = {
                    "name": model_name,
                    "source": source,
                    "device": self.device
                }
                self.logger.info(f"Model {model_name} loaded successfully")
                return True, None
            else:
                self.logger.error(f"Failed to load model: {error}")
                return False, error
            
        except Exception as e:
            error_msg = f"Error loading model: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def generate_refactoring(self, code: str, smells: List[str], model: str = None) -> Tuple[str, Dict]:
        """Generate refactored code using the loaded model with resource monitoring."""
        if not self.model_loaded:
            raise RuntimeError("No model loaded. Please load a model first.")
        
        try:
            # Check resources before generation
            if not self.resource_monitor.check_resources():
                raise RuntimeError("Insufficient resources for code generation")
            
            self.logger.info(f"Starting code refactoring with model {self.current_model['name']}")
            self.logger.info(f"Code smells to address: {smells}")
            
            # Generate with resource monitoring
            with self.resource_monitor.monitor_generation():
                refactored_code, metadata = self.engine.refactor_code(code, smells, model)
            
            # Add resource usage to metadata
            metadata["resource_usage"] = self.resource_monitor.get_generation_stats()
            self.logger.info("Code refactoring completed successfully")
            return refactored_code, metadata
            
        except Exception as e:
            error_msg = f"Error during refactoring: {str(e)}"
            self.logger.error(error_msg)
            st.error(error_msg)
            return code, {"error": str(e), "success": False}

class ResourceMonitor:
    """Monitors and manages system resources."""
    def __init__(self):
        self.start_time = time.time()
        self.generation_stats = {}
        self.loading_stats = {}
    
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
    def monitor_loading(self):
        """Context manager to monitor resource usage during model loading."""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            self.loading_stats = {
                "duration": end_time - start_time,
                "memory_delta": (end_memory - start_memory) / 1024**2,  # MB
                "peak_memory": psutil.virtual_memory().percent
            }
    
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
    
    def get_loading_stats(self) -> Dict[str, float]:
        """Get statistics from the last model loading."""
        return self.loading_stats

# Initialize session state
if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProjectManager()
if 'model_manager' not in st.session_state:
    st.session_state.model_manager = ModelManager()

# Initialize refactoring components in session state
if 'refactor_model' not in st.session_state:
    st.session_state.refactor_model = None
if 'refactoring_engine' not in st.session_state:
    st.session_state.refactoring_engine = RefactoringEngine()
if 'refactoring_manager' not in st.session_state:
    st.session_state.refactoring_manager = RefactoringFileManager()
if 'refactored_paths' not in st.session_state:
    st.session_state.refactored_paths = {}

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
            help="Select where to load the LLM from",
            key="sidebar_model_source"
        )
        
        # Conditional model selection based on source
        if model_source == "Local":
            model = st.selectbox(
                "Select Model",
                ["Code Llama 13B"],
                help="Choose a local model",
                key="sidebar_local_model"
            )
            if st.button("Load Model", key="sidebar_load_model_local"):
                st.session_state.model_manager.load_model("Local", model)
        elif model_source in ["Cloud", "Private Cloud"]:
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Enter your API key",
                key="sidebar_api_key"
            )
            model = st.text_input(
                "Model Name",
                help="Enter the model identifier",
                key="sidebar_model_name"
            )
            if st.button("Load Model", key="sidebar_load_model_cloud"):
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
            selected_smells[smell] = st.checkbox(
                smell,
                value=default,
                key=f"sidebar_smell_{smell.lower().replace(' ', '_')}"
            )
        
        st.divider()
        
        # Refactoring Mode
        st.subheader("Refactoring Mode")
        mode = st.radio(
            "Select Mode",
            ["Manual", "Auto"],
            help="Choose how to apply refactorings",
            key="sidebar_refactoring_mode"
        )
        
        return selected_smells, mode

def render_refactoring_sidebar():
    """Render the refactoring configuration sidebar."""
    st.sidebar.title("⚙️ Model Configuration")
    
    # Model source selection
    model_source = st.sidebar.selectbox(
        "Model Source",
        ["Local", "GPT-Lab", "Private Cloud"],
        help="Select where to load the model from",
        key="refactoring_sidebar_source"
    )
    
    # Model selection and configuration
    model_manager = st.session_state.model_manager
    available_models = model_manager.available_models
    
    # Display endpoints status
    if model_source == "GPT-Lab":
        st.sidebar.markdown("### 🌐 GPT-Lab Endpoints")
        
        # Check endpoint status
        for endpoint_name, endpoint_info in GPTLAB_ENDPOINTS.items():
            if endpoint_name == "LOCAL":  # Skip local endpoint in GPT-Lab section
                continue
                
            # Check endpoint status
            is_active = check_ollama_status(endpoint_name)
            status = "active" if is_active else "offline"
            status_color = "🟢" if is_active else "🔴"
            
            # Create an endpoint status indicator
            col1, col2, col3 = st.sidebar.columns([1, 2, 1])
            with col1:
                st.markdown(f"{status_color}")
            with col2:
                st.markdown(f"{endpoint_name}")
            with col3:
                st.markdown(f"{endpoint_info['hardware']}")
        
        # API key input
        api_key = st.sidebar.text_input(
            "GPT-Lab API Key",
            type="password",
            help="Enter your GPT-Lab API key",
            key="refactoring_sidebar_gptlab_api_key"
        )
        
        # Model selection
        available_gptlab_models = [
            name for name, info in available_models.items() 
            if info.get("type") == "cloud" and info.get("provider") == "GPTlab"
        ]
        if available_gptlab_models:
            selected_model = st.sidebar.selectbox(
                "Select Model",
                available_gptlab_models,
                help="Choose a GPT-Lab model",
                key="refactoring_sidebar_gptlab_model"
            )
            
            # Show model info
            if selected_model:
                model_info = available_models[selected_model]
                st.sidebar.markdown("#### Model Information")
                st.sidebar.markdown(f"- **Endpoint:** {model_info.get('endpoint', 'Unknown')}")
                st.sidebar.markdown(f"- **Hardware:** {model_info.get('hardware', 'Unknown')}")
                st.sidebar.markdown(f"- **Max Tokens:** {model_info.get('max_tokens', 'Unknown')}")
        else:
            st.sidebar.warning("No GPT-Lab models available. Please check your API key and endpoint status.")
            selected_model = None
            
    elif model_source == "Local":
        st.sidebar.markdown("### 💻 Local Models")
        
        # Check Ollama status
        ollama_status = check_ollama_status("LOCAL")
        if not ollama_status:
            st.sidebar.error("❌ Ollama service is not running. Please start Ollama first.")
        else:
            st.sidebar.success("✅ Ollama service is running")
        
        available_local_models = [
            name for name, info in available_models.items() 
            if info.get("type") == "local"
        ]
        if available_local_models:
            selected_model = st.sidebar.selectbox(
                "Select Model",
                available_local_models,
                help="Choose a local model",
                key="refactoring_sidebar_local_model"
            )
            
            # Show model info
            if selected_model:
                model_info = available_models[selected_model]
                st.sidebar.markdown("#### Model Information")
                st.sidebar.markdown(f"- **Provider:** {model_info.get('provider', 'Unknown')}")
                st.sidebar.markdown(f"- **Device:** {model_info.get('device', 'Local')}")
        else:
            st.sidebar.warning("No local models found. Please check Ollama installation.")
            selected_model = None
            
    else:  # Private Cloud
        st.sidebar.markdown("### ☁️ Private Cloud Models")
        available_cloud_models = [
            name for name, info in available_models.items() 
            if info.get("type") == "cloud" and info.get("provider") != "GPTlab"
        ]
        if available_cloud_models:
            selected_model = st.sidebar.selectbox(
                "Select Model",
                available_cloud_models,
                help="Choose a cloud model",
                key="refactoring_sidebar_cloud_model"
            )
            
            # Show model info
            if selected_model:
                model_info = available_models[selected_model]
                st.sidebar.markdown("#### Model Information")
                st.sidebar.markdown(f"- **Provider:** {model_info.get('provider', 'Unknown')}")
                st.sidebar.markdown(f"- **Max Tokens:** {model_info.get('max_tokens', 'Unknown')}")
                st.sidebar.markdown(f"- **Temperature:** {model_info.get('temperature', 0.7)}")
        else:
            st.sidebar.warning("No cloud models available.")
            selected_model = None
    
    # Model parameters
    if selected_model:
        st.sidebar.markdown("### ⚙️ Model Parameters")
        temperature = st.sidebar.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Higher values make output more creative but less focused",
            key="refactoring_sidebar_temperature"
        )
        
        # Load model button
        if st.sidebar.button("Load Model", key="refactoring_sidebar_load_model"):
            with st.sidebar.status("Loading model...") as status:
                try:
                    api_key = st.session_state.get("gptlab_api_key") if model_source == "GPT-Lab" else None
                    success = model_manager.load_model(
                        source=model_source,
                        model_name=selected_model,
                        api_key=api_key
                    )
                    if success:
                        status.update(label="✅ Model loaded successfully!", state="complete")
                        st.session_state.current_model = selected_model
                    else:
                        status.update(label="❌ Failed to load model", state="error")
                except Exception as e:
                    status.update(label=f"❌ Error: {str(e)}", state="error")
    
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
        if st.sidebar.checkbox(
            smell,
            help=description,
            key=f"refactoring_sidebar_smell_{smell.lower().replace(' ', '_')}"
        ):
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

def render_metric_card(label: str, metric: dict, help_text: str = "") -> None:
    status_colors = {
        "low": ("#28a745", "✅"),
        "medium": ("#ffc107", "⚠️"),
        "high": ("#dc3545", "❌")
    }
    color, icon = status_colors.get(metric["status"], ("#6c757d", "ℹ️"))
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {color}; padding: 1rem;">
        <div style="color: #666; font-size: 0.9em;">{metric["icon"]} {label}
            <span title="{help_text}" style="cursor: help; color: #888;"> ⓘ</span>
        </div>
        <div style="font-size: 1.5em; font-weight: bold; color: {color};">
            {metric["value"]} {icon}
        </div>
        <div style="font-size: 0.8em; color: #666;">
            Threshold: {metric.get("threshold", "-")}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
def format_metric_evidence(metric_name: str, value: float, threshold: float, comparison: str = ">") -> str:
    """Format metric evidence with value and threshold."""
    return f"{metric_name} = {value:.2f} {comparison} {threshold:.2f} threshold"

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
        st.error("❌ No Java files found in the project.")
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
                                if chart is not None:
                                    if hasattr(chart, 'show'):
                                        st.plotly_chart(chart, use_container_width=True)
                                    else:
                                        st.bar_chart(chart.set_index('Metric')[['Value', 'Threshold']])
                                else:
                                    st.info("No metrics available for visualization.")
                            except Exception as e:
                                st.error(f"Could not render metrics chart: {str(e)}")
                        
                    except Exception as e:
                        st.error(f"❌ Error displaying analysis results: {str(e)}")
                        return
                
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            return

def render_refactoring_tab():
    """Render the Refactoring tab content with a professional workflow."""
    st.title("🛠️ Code Refactoring")
    
    # Initialize session state variables
    if 'refactoring_step' not in st.session_state:
        st.session_state.refactoring_step = 1
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
        st.warning("⚠️ Please upload a project first in the Project Upload tab.")
        return
    
    # Get Java files from project
    java_files = [f for f in st.session_state.project_manager.project_metadata.get("java_files", []) 
                  if f["path"].endswith(".java")]
    
    if not java_files:
        st.warning("⚠️ No Java files found. Please upload a project with Java files.")
        return

    # Display workflow steps
    steps = ["1. Select File", "2. Analyze Code", "3. Choose Patterns", "4. Preview Changes", "5. Apply Refactoring"]
    current_step = st.session_state.refactoring_step
    
    # Create progress bar
    progress = (current_step - 1) / (len(steps) - 1)
    st.progress(progress)
    
    # Display steps with current step highlighted
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i + 1 == current_step:
                st.markdown(f"**{step}** 🎯")
            else:
                st.markdown(step)
    
    st.divider()

    # Step 1: File Selection
    if current_step == 1:
        st.markdown("### 📁 Select File to Refactor")
        st.caption("Choose a Java file to begin the refactoring process.")
        
        # Search/filter
        search_query = st.text_input("🔍 Search files", placeholder="Type to filter files...")
        filtered_files = [
            f for f in java_files
            if not search_query or search_query.lower() in f["name"].lower() or search_query.lower() in f["path"].lower()
        ]

        # File selection dropdown
        selected_file = st.selectbox(
            "Select a file to refactor",
            options=filtered_files,
            format_func=lambda x: f"📄 {x['path']}",
            key="refactoring_file_selector"
        )

        if selected_file:
            try:
                file_path = Path(st.session_state.project_manager.project_path) / selected_file["path"]
                with open(file_path, 'r') as f:
                    code_content = f.read()
                    st.session_state.original_code = code_content

                # Show file info
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**File:** {selected_file['name']}")
                    st.markdown(f"**Path:** {selected_file['path']}")
                with col2:
                    st.markdown(f"**Size:** {format_file_size(selected_file['size'])}")
                    st.markdown(f"**Last Modified:** {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")

                # Preview code
                with st.expander("📄 Preview Code", expanded=True):
                    st.code(code_content, language="java")

                if st.button("Next: Analyze Code", use_container_width=True):
                    st.session_state.refactoring_step = 2
                    st.session_state.selected_file = selected_file
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return

    # Step 2: Code Analysis
    elif current_step == 2:
        st.markdown("### 🔍 Code Analysis")
        st.caption("Analyzing code quality and identifying potential improvements.")
        
        if not st.session_state.original_code:
            st.error("No code loaded. Please go back and select a file.")
            return
        
        # Run analysis
        with st.spinner("Analyzing code..."):
            # Basic metrics
            basic_metrics = calculate_basic_metrics(st.session_state.original_code)
            advanced_metrics = calculate_advanced_metrics(st.session_state.original_code, basic_metrics)
            
            # --- Professional Advanced Metrics Display (copied from Smell Detection tab) ---
            st.markdown("##### Advanced Metrics")
            metric_categories = {
                "Complexity Metrics": ["cc", "lcom", "cbo", "dit"],
                "Size Metrics": ["loc", "loc_per_method", "max_method_length"],
                "Structure Metrics": ["num_methods", "num_fields", "num_public_methods", "num_public_fields"],
                "Documentation Metrics": ["comment_density"]
            }
            for category, metric_keys in metric_categories.items():
                st.markdown(f"###### {category}")
                cols = st.columns(len(metric_keys))
                for col, metric_key in zip(cols, metric_keys):
                    metric_data = advanced_metrics.get(metric_key)

                    display_value = "-"
                    display_label = metric_key.replace('_', ' ').title()
                    display_icon = ""
                    display_status = "UNKNOWN"
                    status_class = "low"  # Default CSS class for status

                    if isinstance(metric_data, dict):
                        display_value = metric_data.get('value', '-')
                        display_icon = metric_data.get('icon', '')
                        raw_status = metric_data.get('status', 'unknown').lower()
                        if raw_status in ["high", "medium", "low"]:
                            status_class = raw_status
                            display_status = raw_status.upper()
                        elif display_value != '-':
                            display_status = "INFO"
                            status_class = "low"
                        else:
                            display_status = "N/A"
                            status_class = "low"
                    elif isinstance(metric_data, (int, float, str)):
                        display_value = metric_data
                        display_status = "VALUE"
                        status_class = "low"
                    elif metric_data is None:
                        display_value = "N/A"
                        display_status = "MISSING"
                        status_class = "medium"

                    if not isinstance(display_value, str):
                        display_value = str(display_value)

                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{display_value}</div>
                            <div class="metric-label">{display_icon} {display_label}</div>
                            <div class="metric-status status-{status_class}">
                                {display_status}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            # --- End Advanced Metrics Display ---
            
            # Add metrics visualization
            with st.expander("📊 Metric Visualization", expanded=True):
                try:
                    chart = render_metrics_chart(advanced_metrics)
                    if chart is not None:
                        if hasattr(chart, 'show'):
                            st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.bar_chart(chart.set_index('Metric')[['Value', 'Threshold']])
                    else:
                        st.info("No metrics available for visualization.")
                except Exception as e:
                    st.error(f"Could not render metrics chart: {str(e)}")
            
            # Code smells detection
            st.markdown("### 🚨 Detected Code Smells")
            detected_smells = analyze_code_smells(st.session_state.original_code)
            st.session_state.detected_smells = detected_smells
            
            if detected_smells:
                for smell, details in detected_smells.items():
                    with st.expander(f"⚠️ {smell}", expanded=True):
                        st.markdown(f"**Location:** {details['location']}")
                        st.markdown(f"**Description:** {details['description']}")
                        st.markdown(f"**Suggestion:** {details['suggestion']}")
            else:
                st.success("✅ No code smells detected!")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back to File Selection", use_container_width=True):
                    st.session_state.refactoring_step = 1
                    st.rerun()
            with col2:
                if st.button("Next: Choose Patterns →", use_container_width=True):
                    st.session_state.refactoring_step = 3
                    st.rerun()

    # Step 3: Pattern Selection
    elif current_step == 3:
        st.markdown("### 🎯 Choose Refactoring Patterns")
        st.caption("Select the refactoring patterns to apply based on the analysis.")
        
        # Refactoring patterns with descriptions
        refactoring_patterns = {
            "Extract Method": {
                "description": "Split long methods into smaller, focused ones",
                "icon": "🔧",
                "applicable": "Long Method" in [s for s in st.session_state.detected_smells.keys()]
            },
            "Extract Class": {
                "description": "Move related fields and methods to a new class",
                "icon": "📦",
                "applicable": "God Class" in [s for s in st.session_state.detected_smells.keys()]
            },
            "Move Method": {
                "description": "Move method to a more appropriate class",
                "icon": "↗️",
                "applicable": "Feature Envy" in [s for s in st.session_state.detected_smells.keys()]
            },
            "Encapsulate Field": {
                "description": "Make fields private and provide accessors",
                "icon": "🔒",
                "applicable": "Data Class" in [s for s in st.session_state.detected_smells.keys()]
            },
            "Replace Conditional with Polymorphism": {
                "description": "Use inheritance instead of conditionals",
                "icon": "🔄",
                "applicable": "Complex Class" in [s for s in st.session_state.detected_smells.keys()]
            }
        }
        
        # Display patterns in a grid
        cols = st.columns(2)
        selected_patterns = []
        
        for i, (pattern, info) in enumerate(refactoring_patterns.items()):
            with cols[i % 2]:
                if st.checkbox(
                    f"{info['icon']} {pattern}",
                    help=info["description"],
                    disabled=not info["applicable"],
                    key=f"pattern_{pattern}"
                ):
                    selected_patterns.append(pattern)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Analysis", use_container_width=True):
                st.session_state.refactoring_step = 2
                st.rerun()
        with col2:
            if st.button("Next: Preview Changes →", use_container_width=True):
                st.session_state.refactoring_step = 4
                st.session_state.selected_patterns = selected_patterns
                st.rerun()

    # Step 4: Preview Changes
    elif current_step == 4:
        st.markdown("### 👀 Preview Changes")
        st.caption("Review the proposed changes before applying them.")

        # Model selection for refactoring (under Preview Changes)
        st.markdown("#### Select LLM Model for Refactoring")
        selected_model = st.selectbox(
            "Choose a model:",
            MODEL_OPTIONS,
            key="refactoring_model_preview",
            help="Choose which LLM to use for this refactoring"
        )
        rerun_refactor = False
        if 'selected_model' not in st.session_state or st.session_state['selected_model'] != selected_model:
            st.session_state['selected_model'] = selected_model
            rerun_refactor = True
        else:
            selected_model = st.session_state['selected_model']

        # Only rerun refactoring if model changed or not yet run
        if rerun_refactor or 'last_refactored_model' not in st.session_state or st.session_state['last_refactored_model'] != selected_model:
            st.session_state['last_refactored_model'] = selected_model
            # Generate refactored code
            with st.spinner("Generating refactored code..."):
                refactored_code, metadata = generate_refactoring(
                    st.session_state.original_code,
                    st.session_state.selected_patterns,
                    st.session_state.detected_smells
                )
                st.session_state.refactored_code = refactored_code
                st.session_state.refactoring_metadata = metadata

        # Display side-by-side comparison
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Original Code")
            st.code(st.session_state.original_code, language="java")
        with col2:
            st.markdown("### Refactored Code")
            st.code(st.session_state.refactored_code, language="java")

        # Show changes
        st.markdown("### 📊 Changes Summary")
        render_refactoring_preview(st.session_state.original_code, st.session_state.refactored_code)

        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Patterns", use_container_width=True):
                st.session_state.refactoring_step = 3
                st.rerun()
        with col2:
            if st.button("Next: Apply Refactoring →", use_container_width=True):
                st.session_state.refactoring_step = 5
                st.rerun()

    # Step 5: Apply Refactoring
    elif current_step == 5:
        st.markdown("### ✅ Apply Refactoring")
        st.caption("Apply the refactoring changes to your code.")
        
        if not st.session_state.refactored_code:
            st.error("No refactored code available. Please go back and complete previous steps.")
            return
        
        # Confirmation
        st.markdown("### Are you sure you want to apply these changes?")
        st.markdown("The following changes will be made:")
        
        # Show changes summary
        render_refactoring_preview(st.session_state.original_code, st.session_state.refactored_code)
        
        # Apply changes
        if st.button("Apply Changes", type="primary", use_container_width=True):
            try:
                # Save refactored code
                file_path = Path(st.session_state.project_manager.project_path) / st.session_state.selected_file["path"]
                with open(file_path, 'w') as f:
                    f.write(st.session_state.refactored_code)
                
                # Update history
                st.session_state.refactoring_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file": st.session_state.selected_file["path"],
                    "patterns": st.session_state.selected_patterns,
                    "before_metrics": calculate_basic_metrics(st.session_state.original_code),
                    "after_metrics": calculate_basic_metrics(st.session_state.refactored_code)
                })
                
                st.success("✅ Refactoring applied successfully!")
                
                # Reset workflow
                st.session_state.refactoring_step = 1
                st.rerun()
                
            except Exception as e:
                st.error(f"Error applying changes: {str(e)}")
        
        # Navigation buttons
        if st.button("← Back to Preview", use_container_width=True):
            st.session_state.refactoring_step = 4
            st.rerun()

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
        ✅ UserManagerTest: 12/12 passed
        ✅ DataServiceTest: 8/8 passed
        ✅ UtilsTest: 5/5 passed
        """)
    
    # Performance Comparison
    st.markdown("### Performance Comparison")
    # TODO: Implement real performance metrics
    st.line_chart({
        "Before": [75, 82, 78, 85, 90],
        "After": [85, 89, 88, 92, 95]
    })

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

# --- Static list of available GPT-Lab models (from gptlab_test.py) ---
MODEL_OPTIONS = [
    "llama3.2",
    "llama3.1:70b-instruct-q4_K_M",
    "codellama:7b",
    "codegemma:7b",
    "deepseek-coder:6.7b",
    "phi4:14b-fp16",
    "GPT-Lab/Viking-33B-cp2000B-GGUF:Q6_K",
    "magicoder:7b"
]

def calculate_basic_metrics(content: str) -> dict:
    """Calculate basic code metrics for a Java file."""
    try:
        # Initialize metrics
        metrics = {
            "loc": 0,  # Lines of Code
            "total_methods": 0,  # Total number of methods
            "wmc": 0,  # Weighted Methods per Class
            "getters_setters": 0,  # Number of getters and setters
            "loc_threshold": 200,  # Threshold for LOC
            "wmc_threshold": 20,  # Threshold for WMC
            "methods_threshold": 5  # Threshold for number of methods
        }
        
        # Count lines of code (excluding comments and empty lines)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('//') and not line.startswith('/*') and not line.startswith('*'):
                metrics["loc"] += 1
        
        # Count methods and calculate WMC
        method_pattern = r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{'
        methods = re.finditer(method_pattern, content)
        
        for method in methods:
            metrics["total_methods"] += 1
            
            # Calculate method complexity (simple version)
            method_content = content[method.start():]
            method_end = method_content.find('}')
            if method_end != -1:
                method_content = method_content[:method_end]
                complexity = len(re.findall(r'\b(if|for|while|case|catch)\b', method_content))
                metrics["wmc"] += complexity
            
            # Count getters and setters
            method_name = method.group(4)
            if method_name.startswith('get') or method_name.startswith('set'):
                metrics["getters_setters"] += 1
        
        return metrics
        
    except Exception as e:
        st.error(f"Error calculating basic metrics: {str(e)}")
        return {
            "loc": 0,
            "total_methods": 0,
            "wmc": 0,
            "getters_setters": 0,
            "loc_threshold": 200,
            "wmc_threshold": 20,
            "methods_threshold": 5
        }

def analyze_code_smells(content: str) -> dict:
    """Analyze code and return a dictionary of detected code smells with details."""
    smells = {}
    metrics = calculate_basic_metrics(content)
    adv_metrics = calculate_advanced_metrics(content, metrics)
    # God Class: Large LOC and many methods
    if metrics["loc"] > 200 and metrics["total_methods"] > 10:
        smells["God Class"] = {
            "location": "Class",
            "description": "Class is very large and does too much.",
            "suggestion": "Consider splitting into smaller classes."
        }
    # Long Method: Any method with >40 lines
    long_methods = re.findall(r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{([\s\S]*?)}', content)
    for m in long_methods:
        method_body = m[4]
        if len(method_body.split('\n')) > 40:
            smells["Long Method"] = {
                "location": f"Method: {m[3]}",
                "description": "Method is too long.",
                "suggestion": "Extract smaller methods."
            }
            break
    # Data Class: Many getters/setters, few other methods
    if metrics["total_methods"] > 0 and metrics["getters_setters"] / metrics["total_methods"] > 0.7:
        smells["Data Class"] = {
            "location": "Class",
            "description": "Class mainly contains data and accessors.",
            "suggestion": "Add behavior or refactor responsibilities."
        }
    # Feature Envy: Many external calls (very basic heuristic)
    if len(re.findall(r'\w+\.\w+\(', content)) > 10:
        smells["Feature Envy"] = {
            "location": "Methods",
            "description": "Methods use many features of other classes.",
            "suggestion": "Move methods to more appropriate classes."
        }
    # Complex Class: Many branches
    if len(re.findall(r'\b(if|for|while|case|catch)\b', content)) > 30:
        smells["Complex Class"] = {
            "location": "Class",
            "description": "Class has high cyclomatic complexity.",
            "suggestion": "Simplify logic or split class."
        }
    # Long Parameter List
    long_params = re.findall(r'\(([^)]{40,})\)', content)
    if long_params:
        smells["Long Parameter List"] = {
            "location": "Methods",
            "description": "Methods with too many parameters.",
            "suggestion": "Refactor to use parameter objects."
        }
    # Duplicate Code (simple: repeated lines)
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) != len(set(lines)):
        smells["Duplicate Code"] = {
            "location": "Class/Methods",
            "description": "Duplicate lines of code detected.",
            "suggestion": "Refactor to remove duplication."
        }
    # Switch Statements
    if re.search(r'switch\s*\(', content):
        smells["Switch Statements"] = {
            "location": "Methods",
            "description": "Switch/case statements detected.",
            "suggestion": "Consider polymorphism or strategy pattern."
        }
    # Too Many Fields
    if adv_metrics["num_fields"]["value"] > 15:
        smells["Too Many Fields"] = {
            "location": "Class",
            "description": "Class has too many fields/attributes.",
            "suggestion": "Split class or reduce fields."
        }
    # Lazy Class
    if metrics["loc"] < 50 and metrics["total_methods"] < 3:
        smells["Lazy Class"] = {
            "location": "Class",
            "description": "Class does too little.",
            "suggestion": "Remove or merge with another class."
        }
    # Message Chains
    if len(re.findall(r'\w+\.\w+\.\w+', content)) > 5:
        smells["Message Chains"] = {
            "location": "Methods",
            "description": "Chained method calls detected.",
            "suggestion": "Refactor to reduce message chains."
        }
    # Middle Man
    if metrics["total_methods"] > 0 and adv_metrics["num_fields"]["value"] > 0 and metrics["total_methods"] / adv_metrics["num_fields"]["value"] < 0.5:
        smells["Middle Man"] = {
            "location": "Class",
            "description": "Class delegates most of its work.",
            "suggestion": "Remove unnecessary delegation."
        }
    return smells

def generate_refactoring(original_code, selected_patterns, detected_smells):
    """
    Generate refactored code using GPT-Lab or local LLM.
    Returns (refactored_code, metadata).
    """
    if not selected_patterns:
        return original_code, {"success": False, "reason": "No patterns selected."}
    # Prepare additional instructions
    instructions = f"Apply the following refactoring patterns: {', '.join(selected_patterns)}."
    # Use detected smells as context
    try:
        st.info(f"Prompt being sent to LLM:\n{instructions}")
        # Force use of GPT-Lab model
        model_to_use = st.session_state.get('selected_model', MODEL_OPTIONS[0])
        st.info(f"Using GPT-Lab model: {model_to_use}")
        refactored_code = refactor_with_gptlab(
            code=original_code,
            model_name=model_to_use,
            smell_analysis=detected_smells,
            additional_instructions=instructions,
            temperature=st.session_state.get('refactoring_sidebar_temperature', 0.3)
        )
        st.info(f"LLM response:\n{refactored_code[:500]}")  # Show first 500 chars
        return refactored_code, {"success": True, "patterns": selected_patterns}
    except Exception as e:
        return original_code, {"success": False, "reason": str(e)}

GPTLAB_ENDPOINTS = {
    "CLOUD": {
        "url": "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM/v1",
        "hardware": "Cloud GPU",
        "status": "active"
    }
}
GPTLAB_BEARER_TOKEN = "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d"

if __name__ == "__main__":
    main() 