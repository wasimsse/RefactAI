#!/bin/bash
# Startup script for RefactAI Agents Service

cd "$(dirname "$0")"

# Set OpenRouter API key if not already set
if [ -z "$OPENROUTER_API_KEY" ]; then
    export OPENROUTER_API_KEY="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"
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

