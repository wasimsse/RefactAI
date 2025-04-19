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
from smell_detector.detector import detect_smells

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
    """Manages LLM model loading and operations."""
    def __init__(self):
        self.model = None
        self.model_source = "Local"
        self.model_name = "Code Llama 13B"
    
    def load_model(self, source: str, model_name: str, api_key: Optional[str] = None) -> bool:
        """Load the specified model."""
        try:
            # TODO: Implement real model loading logic
            self.model_source = source
            self.model_name = model_name
            return True
        except Exception as e:
            st.error(f"Error loading model: {str(e)}")
            return False
    
    def generate_refactoring(self, code: str, smell_type: str) -> str:
        """Generate refactoring suggestions using the model."""
        try:
            # TODO: Implement real refactoring generation
            return code
        except Exception as e:
            st.error(f"Error generating refactoring: {str(e)}")
            return code

# Initialize session state
if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProjectManager()
if 'model_manager' not in st.session_state:
    st.session_state.model_manager = ModelManager()

def render_sidebar():
    """Render the sidebar with model selection and configuration options."""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Model Source Selection
        model_source = st.selectbox(
            "Model Source",
            ["Local", "Cloud", "Private Cloud"],
            help="Select where to load the LLM from"
        )
        
        # Conditional model selection based on source
        if model_source == "Local":
            model = st.selectbox(
                "Select Model",
                ["Code Llama 13B", "StarCoder 7B", "DeepSeek 6.7B"],
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
        model_status = "Active ✅" if st.session_state.model_manager.model else "Inactive ❌"
        st.metric(
            "Model Status",
            model_status,
            st.session_state.model_manager.model_name
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
                    with st.spinner("Analyzing code smells..."):
                        try:
                            results = detect_smells([{
                                "class_name": selected_file["name"],
                                "content": file_content,
                                "inheritance_data": {
                                    "inherited_methods": 5,
                                    "used_methods": 2,
                                    "overridden_methods": 3
                                }
                            }])
                            
                            st.session_state.analysis_results = results[selected_file["name"]]
                            st.session_state.show_analysis = True
                            st.toast("✅ Analysis complete!")
                        except Exception as e:
                            st.error(f"❌ Error during analysis: {str(e)}")
                            return
                
                # Display Analysis Results
                if st.session_state.show_analysis and st.session_state.analysis_results:
                    metrics = st.session_state.analysis_results["metrics"]
                    
                    # Add class type information to metrics
                    metric_cols = st.columns(4)
                    metrics_data = [
                        ("Total Classes", file_classes['total'], "🔷"),
                        ("Lines of Code", metrics["loc"], "📏"),
                        ("Total Methods", metrics["total_methods"], "🔧"),
                        ("Complexity (WMC)", metrics["wmc"], "🔄")
                    ]
                    
                    for col, (label, value, icon) in zip(metric_cols, metrics_data):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                            <h3>{icon} {value}</h3>
                            <small>{label}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Detected Smells Section
                    st.markdown("##### 🚨 Detected Code Smells")
                    if st.session_state.analysis_results["smells"]:
                        for smell in st.session_state.analysis_results["smells"]:
                            smell_color = {
                                "God Class": ("🔴", "#dc3545"),
                                "Data Class": ("🟡", "#ffc107"),
                                "Lazy Class": ("🟠", "#fd7e14"),
                                "Feature Envy": ("🟣", "#6f42c1"),
                                "Refused Bequest": ("🔵", "#0d6efd")
                            }.get(smell, ("⚪", "#6c757d"))
                            
                            st.markdown(f"""
                            <div class="smell-card">
                            <h4 style="color: {smell_color[1]}">{smell_color[0]} {smell}</h4>
                            <p><i>{st.session_state.analysis_results['reasoning'][smell]}</i></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("✅ No code smells detected in this file")
                    
                    # Quick Actions
                    st.markdown("##### 🛠️ Quick Actions")
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button("📋 Copy Analysis Report", use_container_width=True):
                            # Create report text with class information
                            report = f"""
                            Code Smell Analysis Report
                            File: {selected_file['path']}
                            Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            
                            Class Information:
                            - Total Classes: {file_classes['total']}
                            """
                            
                            for class_type, classes in file_classes['types'].items():
                                if classes:
                                    report += f"\n{class_type.title()}s: {', '.join(classes)}"
                            
                            report += f"""
                            
                            Metrics:
                            - Lines of Code: {metrics['loc']}
                            - Total Methods: {metrics['total_methods']}
                            - Public Methods: {metrics['public_methods']}
                            - Complexity (WMC): {metrics['wmc']}
                            
                            Detected Smells:
                            """
                            
                            for smell in st.session_state.analysis_results["smells"]:
                                report += f"\n{smell}:\n{st.session_state.analysis_results['reasoning'][smell]}\n"
                            
                            # Copy to clipboard (through JavaScript)
                            st.markdown(f"""
                            <script>
                            navigator.clipboard.writeText(`{report}`);
                            </script>
                            """, unsafe_allow_html=True)
                            st.toast("📋 Report copied to clipboard!")
                    
                    with action_col2:
                        if st.button("🔄 Rerun Analysis", use_container_width=True):
                            st.session_state.show_analysis = False
                            st.experimental_rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            return

def render_refactoring_tab():
    """Render the Refactoring tab content."""
    st.title("🛠️ Code Refactoring")
    
    if not st.session_state.project_manager.project_path:
        st.warning("Please upload a project first")
        return
    
    # Class Selection
    selected_class = st.selectbox(
        "Select Class to Refactor",
        ["UserManager.java", "DataService.java", "Utils.java"]
    )
    
    # Code Display
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Original Code")
        # TODO: Implement real code loading
        st.code("""
public class UserManager {
    // Original implementation
}
        """, language="java")
        
    with col2:
        st.markdown("### Refactored Code")
        refactored_code = st.text_area(
            "Edit refactored code",
            value="""
public class UserManager {
    // Refactored implementation
}
            """,
            height=300
        )
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✨ Apply Refactoring"):
            # TODO: Implement real refactoring application
            st.success("Refactoring applied!")
    with col2:
        if st.button("↩️ Revert Changes"):
            # TODO: Implement real change reversion
            st.success("Changes reverted!")
    with col3:
        if st.button("💾 Save to File"):
            # TODO: Implement real file saving
            st.success("Changes saved!")

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