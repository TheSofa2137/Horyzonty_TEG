#!/bin/bash

# Backend startup script - Start only the backend

echo "🔌 Starting Horyzonty Backend..."
echo ""

cd "$(dirname "$0")/backend"

# Check if venv exists, if not create it
if [ ! -d "../venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv ../venv
fi

# Activate venv
source ../venv/bin/activate

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn python-dotenv langchain langchain-community langchain-ollama langchain-text-splitters chromadb

echo ""
echo "🔌 Starting FastAPI server..."
echo ""
echo "✨ Backend will start at: http://localhost:8000"
echo "📚 API Docs available at: http://localhost:8000/docs"
echo ""
echo "Make sure Ollama is running: ollama serve"
echo ""

# Use the test WebSocket server by default (easy testing)
echo "💡 Using test backend for quick testing"
echo "   (Replace with 'main:app' in production)"
echo ""

python -m uvicorn test_websocket:app --reload --host 0.0.0.0 --port 8000

