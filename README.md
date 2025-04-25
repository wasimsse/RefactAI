# RefactAI

RefactAI is an intelligent code refactoring assistant that helps developers detect and fix code smells in Java projects using state-of-the-art Large Language Models (LLMs).

## Features

- 🔍 **Code Smell Detection**: Automatically identify common anti-patterns in Java code
- 🤖 **AI-Powered Refactoring**: Get intelligent suggestions for code improvements
- 📊 **Quality Metrics**: Track code quality improvements over time
- 🧪 **Testing Integration**: Ensure refactoring changes maintain code quality
- 🔄 **Multiple Model Support**: Choose from various LLM models (local or cloud-based)
- 🔒 **Secure Configuration**: Environment-based configuration for sensitive settings

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- Required Python packages (see requirements.txt)
- Access to GPTlab/Ollama server (optional)

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

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
streamlit run dashboard.py
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```ini
# GPTlab/Ollama Configuration
GPTLAB_BASE_URL=http://localhost:11434  # Your GPTlab/Ollama server URL
GPTLAB_API_KEY=your-api-key-here        # Your API key if required

# Other Configuration
DEBUG=False
LOG_LEVEL=INFO
```

## Security

- Never commit your `.env` file or any files containing API keys
- The `.gitignore` file is configured to exclude sensitive files
- Use environment variables for all sensitive configuration
- Default to local models if no API keys are configured

## Usage

1. Configure your environment using the `.env` file
2. Upload your Java project through the interface
3. Select the code smells you want to detect
4. Choose your preferred LLM model (local or cloud)
5. Run the analysis
6. Review and apply suggested refactorings

## Model Support

The application supports multiple model sources:

- **Local**: Run models locally using Ollama
- **Cloud**: Use cloud-based LLM providers
- **Private Cloud**: Connect to private GPTlab instances

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. When contributing:

1. Fork the repository
2. Create a new branch for your feature
3. Add your changes
4. Submit a pull request
5. Ensure no sensitive information is included

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to the Ollama project for local model support
- Thanks to the GPTlab team for cloud model integration 