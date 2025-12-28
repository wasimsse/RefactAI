#!/bin/bash
# Startup script for RefactAI Agents Service

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# SINGLE SOURCE OF TRUTH: Load API key from agents/.env file ONLY
# This is the ONLY place you need to paste your OpenRouter API key
# File: agents/.env
# Content: OPENROUTER_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE
if [ -z "$OPENROUTER_API_KEY" ]; then
    ENV_FILE="$SCRIPT_DIR/.env"
    if [ -f "$ENV_FILE" ]; then
        # Load .env file (simple parsing, no comments or spaces)
        export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
    fi
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "======================================================================"
        echo "❌ ERROR: OPENROUTER_API_KEY not found!"
        echo "======================================================================"
        echo ""
        echo "📍 SINGLE PLACE TO PASTE YOUR KEY:"
        echo "   File: agents/.env"
        echo "   Full path: $ENV_FILE"
        echo ""
        echo "📝 Create the file with this content (ONE line only):"
        echo "   OPENROUTER_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE"
        echo ""
        echo "💡 Quick command:"
        echo "   echo 'OPENROUTER_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE' > $ENV_FILE"
        echo ""
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

