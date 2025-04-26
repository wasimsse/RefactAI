# RefactAI

A powerful code refactoring tool powered by GPTlab that helps detect and fix code smells in Java projects.

## Features

- 🔍 Code Smell Detection
- 🛠️ Automated Refactoring
- 📊 Quality Metrics Analysis
- 🧪 Testing Integration
- 🔄 Multiple Model Support

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RefactAI.git
cd RefactAI
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your GPTlab API key:
Create a `.env` file in the project root and add:
```
API_KEY_TOKEN=your_gptlab_api_key
```

## Usage

1. Start the application:
```bash
streamlit run dashboard.py
```

2. Upload your Java project:
   - Use ZIP upload
   - Connect to GitHub repository
   - Upload individual files

3. Select the Refactoring tab to:
   - Choose hardware resources
   - Select target files
   - Pick code smells to address
   - Generate and apply refactoring

## Requirements

- Python 3.8+
- Streamlit
- GPTlab API access
- Java project for analysis

## License

MIT License - see LICENSE file for details 