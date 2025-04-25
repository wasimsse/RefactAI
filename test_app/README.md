# Code Refactoring Model Tester

A simple Streamlit application to test different code refactoring models.

## Features

- Select and load different code models
- Upload Java files for refactoring
- View original and refactored code
- Download refactored code

## Available Models

- CodeGemma 2B
- Code Llama 7B
- DeepSeek Coder 6.7B
- StarCoder2 3B
- Qwen2.5-Coder 3B

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Select a model from the sidebar
2. Click "Load Model" to load the selected model
3. Upload a Java file using the file uploader
4. Click "Refactor Code" to perform refactoring
5. View the refactored code and download if needed

## Directory Structure

- `models/` - Contains the downloaded models
- `uploads/` - Stores uploaded Java files
- `results/` - Stores refactored code results 