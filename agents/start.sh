#!/bin/bash
# Startup script for RefactAI Agents Service

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load API key from environment variable or .env file
# DO NOT hardcode API keys in this file!
if [ -z "$OPENROUTER_API_KEY" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        # Load .env file (simple parsing, no comments or spaces)
        export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -v '^$' | xargs)
    fi
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "❌ ERROR: OPENROUTER_API_KEY not set!"
        echo "   Set it via: export OPENROUTER_API_KEY='your-key-here'"
        echo "   Or create agents/.env file with: OPENROUTER_API_KEY=your-key-here"
        exit 1
    fi
fi

# Set defaults if not provided
export BACKEND_BASE="${BACKEND_BASE:-http://localhost:8083/api}"
export OPENROUTER_MODEL="${OPENROUTER_MODEL:-anthropic/claude-3.5-sonnet}"
export PORT="${PORT:-8091}"

echo "🚀 Starting RefactAI Agents Service..."
echo "   Port: $PORT"
echo "   Model: $OPENROUTER_MODEL"
echo "   Backend: $BACKEND_BASE"
echo "   OpenRouter Key: ${OPENROUTER_API_KEY:0:15}...${OPENROUTER_API_KEY: -4}"
echo ""

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload

