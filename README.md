# RefactAI

RefactAI is an intelligent code refactoring assistant that helps developers detect and fix code smells in Java projects using state-of-the-art Large Language Models (LLMs).

## Features

- 🔍 **Code Smell Detection**: Automatically identify common anti-patterns in Java code
- 🤖 **AI-Powered Refactoring**: Get intelligent suggestions for code improvements
- 📊 **Quality Metrics**: Track code quality improvements over time
- 🧪 **Testing Integration**: Ensure refactoring changes maintain code quality
- 🔄 **Multiple Model Support**: Choose from various LLM models (Code Llama, StarCoder, etc.)

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/wasimsse/RefactAI.git
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

4. Run the application:
```bash
streamlit run dashboard.py
```

## Usage

1. Upload your Java project through the interface
2. Select the code smells you want to detect
3. Choose your preferred LLM model
4. Run the analysis
5. Review and apply suggested refactorings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 