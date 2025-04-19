import streamlit as st
import os
from pathlib import Path

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
        for smell, default in smells.items():
            st.checkbox(smell, value=default)
        
        st.divider()
        
        # Refactoring Mode
        st.subheader("Refactoring Mode")
        mode = st.radio(
            "Select Mode",
            ["Manual", "Auto"],
            help="Choose how to apply refactorings"
        )

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
        st.metric(
            "Model Status",
            "Active ✅",
            "Running on GPU"
        )
    with col2:
        st.metric(
            "Memory Usage",
            "8.2 GB",
            "2.1 GB free"
        )
    with col3:
        st.metric(
            "Classes Analyzed",
            "12",
            "+3 from last run"
        )
    
    # Project Overview
    with st.expander("📊 Project Overview", expanded=True):
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.markdown("### Current Project")
            st.info("example-project.zip")
            st.markdown("- **Total Classes:** 15")
            st.markdown("- **Lines of Code:** 2,341")
            
        with stats_col2:
            st.markdown("### Detected Issues")
            st.warning("- 3 God Classes")
            st.warning("- 2 Feature Envy")
            st.warning("- 1 Data Class")

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
        
    elif method == "GitHub Repository":
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repo",
            help="Enter the URL of your GitHub repository"
        )
        branch = st.text_input("Branch (optional)", value="main")
        
    else:  # Individual Files
        uploaded_files = st.file_uploader(
            "Upload Java Files",
            type="java",
            accept_multiple_files=True,
            help="Upload one or more Java source files"
        )
    
    # Project Loading
    col1, col2 = st.columns(2)
    with col1:
        st.button("📥 Load Project", use_container_width=True)
    with col2:
        st.button("👁️ Preview Files", use_container_width=True)
    
    # File Explorer
    with st.expander("🌳 Project Structure", expanded=True):
        st.markdown("""
        ```
        src/
        ├── main/
        │   └── java/
        │       ├── com/
        │       │   └── example/
        │       │       ├── UserManager.java
        │       │       ├── DataService.java
        │       │       └── Utils.java
        └── test/
            └── java/
                └── com/
                    └── example/
                        └── UserManagerTest.java
        ```
        """)

def render_detection_tab():
    """Render the Smell Detection tab content."""
    st.title("🔍 Code Smell Detection")
    
    # Control Panel
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("🔄 Run Detection", use_container_width=True)
    with col2:
        st.button("💾 Save Results", use_container_width=True)
    with col3:
        st.button("📋 Copy Report", use_container_width=True)
    
    # Results Table
    st.markdown("### Detected Smells")
    st.dataframe({
        "Class": ["UserManager", "DataService", "Utils"],
        "Smells": ["God Class", "Feature Envy", "None"],
        "Confidence": ["95%", "87%", "N/A"],
        "LOC": [523, 245, 89]
    })
    
    # Detailed Analysis
    with st.expander("📝 Detailed Analysis", expanded=True):
        st.code("""
public class UserManager {
    private UserRepository userRepo;
    private AuthService authService;
    private EmailService emailService;
    // God Class: Too many responsibilities
    ...
}
        """, language="java")

def render_refactoring_tab():
    """Render the Refactoring tab content."""
    st.title("🛠️ Code Refactoring")
    
    # Class Selection
    st.selectbox(
        "Select Class to Refactor",
        ["UserManager.java", "DataService.java", "Utils.java"]
    )
    
    # Code Display
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Original Code")
        st.code("""
public class UserManager {
    // Original implementation
}
        """, language="java")
        
    with col2:
        st.markdown("### Refactored Code")
        st.text_area(
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
        st.button("✨ Apply Refactoring", use_container_width=True)
    with col2:
        st.button("↩️ Revert Changes", use_container_width=True)
    with col3:
        st.button("💾 Save to File", use_container_width=True)

def render_testing_tab():
    """Render the Testing & Metrics tab content."""
    st.title("🧪 Testing & Metrics")
    
    # Test Controls
    col1, col2 = st.columns(2)
    with col1:
        st.button("▶️ Run Tests", use_container_width=True)
    with col2:
        st.button("📊 Generate Report", use_container_width=True)
    
    # Metrics Display
    st.markdown("### Quality Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    with metrics_col1:
        st.metric("Code Coverage", "78%", "+5%")
    with metrics_col2:
        st.metric("Complexity", "24", "-8")
    with metrics_col3:
        st.metric("Maintainability", "A", "↑ from B")
    
    # Test Results
    with st.expander("🔍 Test Results", expanded=True):
        st.markdown("""
        ✅ UserManagerTest: 12/12 passed
        ✅ DataServiceTest: 8/8 passed
        ✅ UtilsTest: 5/5 passed
        """)
    
    # Performance Comparison
    st.markdown("### Performance Comparison")
    st.line_chart({
        "Before": [75, 82, 78, 85, 90],
        "After": [85, 89, 88, 92, 95]
    })

def main():
    """Main function to run the Streamlit dashboard."""
    # Render sidebar
    render_sidebar()
    
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