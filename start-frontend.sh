#!/bin/bash

# Development startup script - Start only the frontend

echo "🚀 Starting Horyzonty Frontend..."
echo ""

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "⚛️  Starting React development server..."
echo ""
echo "✨ Frontend will open at: http://localhost:3000"
echo ""
echo "Make sure your backend is running at: ws://localhost:8000/ws"
echo ""

npm start

