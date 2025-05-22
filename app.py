import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import json
import subprocess
import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html
import base64
from io import StringIO
import sys
import traceback
import logging
from typing import Dict, List, Optional, Tuple, Union
import time
from streamlit.runtime.scriptrunner import get_script_run_ctx
import threading
import queue
import uuid
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp
from functools import partial
import signal
import psutil
import gc
import memory_profiler
import line_profiler
import cProfile
import pstats
import io
import tracemalloc
import objgraph
import weakref
import sys
import os
import gc
import time
import threading
import queue
import uuid
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp
from functools import partial
import signal
import psutil
import gc
import memory_profiler
import line_profiler
import cProfile
import pstats
import io
import tracemalloc
import objgraph
import weakref

# Set page config
st.set_page_config(
    page_title="CodeRefactAI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display logo at the top of the welcome section
st.markdown(
    "<div style='text-align: center;'><img src='assets/logo.png' width='180' style='margin-bottom: 1rem;'/></div>",
    unsafe_allow_html=True
)

# Welcome Section
st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: #00FF9D; font-size: 2.5rem; margin-bottom: 1rem;'>🚀 Welcome to CodeRefactAI</h1>
        <p style='color: #FFFFFF; font-size: 1.2rem; margin-bottom: 1.5rem;'>
            Your intelligent code analysis and refactoring companion powered by state-of-the-art LLMs
        </p>
    </div>
""", unsafe_allow_html=True)

# Features Section
st.markdown("""
    <div style='background: #2D2D2D; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h2 style='color: #00FF9D; margin-bottom: 1rem;'>✨ Key Features</h2>
        <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;'>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>🔍 Advanced Code Analysis</h3>
                <p style='color: #FFFFFF;'>Detect code smells, anti-patterns, and potential improvements in your Java projects</p>
            </div>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>🤖 AI-Powered Refactoring</h3>
                <p style='color: #FFFFFF;'>Get intelligent suggestions for code improvements with detailed explanations</p>
            </div>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>🧪 Comprehensive Testing</h3>
                <p style='color: #FFFFFF;'>Integrated JUnit and JaCoCo support for test coverage and quality metrics</p>
            </div>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>📊 Smart Impact Assessment</h3>
                <p style='color: #FFFFFF;'>Analyze ripple effects of proposed changes across your codebase</p>
            </div>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>🔄 Interactive Workflow</h3>
                <p style='color: #FFFFFF;'>Step-by-step guided refactoring process with preview and rollback capabilities</p>
            </div>
            <div style='background: #1E1E1E; padding: 1rem; border-radius: 8px;'>
                <h3 style='color: #00FF9D; margin-bottom: 0.5rem;'>📝 Detailed Reporting</h3>
                <p style='color: #FFFFFF;'>Export refactoring reports, diffs, and metrics for better documentation</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Get Started Section
st.markdown("""
    <div style='text-align: center; background: #2D2D2D; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h2 style='color: #00FF9D; margin-bottom: 1rem;'>🎯 Get Started</h2>
        <p style='color: #FFFFFF; font-size: 1.1rem;'>
            Upload your code, explore our analysis tools, and let AI guide you towards cleaner, more maintainable code.
        </p>
    </div>
""", unsafe_allow_html=True)

# File Upload Section 