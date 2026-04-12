#!/bin/bash

# Frontend Setup Verification Checklist

echo "🔍 Horyzonty Frontend - Setup Verification"
echo "=========================================="
echo ""

# Check Node.js
echo -n "📦 Node.js installed: "
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ $node_version"
else
    echo "❌ Not installed - install from nodejs.org"
fi

# Check npm
echo -n "📦 npm installed: "
if command -v npm &> /dev/null; then
    npm_version=$(npm --version)
    echo "✅ $npm_version"
else
    echo "❌ Not installed"
fi

# Check frontend directory
echo -n "📁 Frontend directory: "
if [ -d "frontend" ]; then
    echo "✅ Found"
else
    echo "❌ Not found"
    exit 1
fi

# Check node_modules
echo -n "📚 Dependencies installed: "
if [ -d "frontend/node_modules" ]; then
    echo "✅ Yes"
else
    echo "❌ Run: cd frontend && npm install"
fi

# Check key files
echo -n "📄 App.tsx: "
[ -f "frontend/src/App.tsx" ] && echo "✅" || echo "❌"

echo -n "📄 ChatInterface.tsx: "
[ -f "frontend/src/components/ChatInterface.tsx" ] && echo "✅" || echo "❌"

echo -n "📄 package.json: "
[ -f "frontend/package.json" ] && echo "✅" || echo "❌"

echo -n "📄 .env: "
[ -f "frontend/.env" ] && echo "✅" || echo "❌"

# Check scripts
echo -n "🚀 start.sh: "
[ -f "start.sh" ] && echo "✅" || echo "❌"

echo -n "🚀 start-frontend.sh: "
[ -f "start-frontend.sh" ] && echo "✅" || echo "❌"

echo -n "🚀 start-backend.sh: "
[ -f "start-backend.sh" ] && echo "✅" || echo "❌"

# Check documentation
echo -n "📚 GETTING_STARTED.md: "
[ -f "GETTING_STARTED.md" ] && echo "✅" || echo "❌"

echo -n "📚 FRONTEND_README.md: "
[ -f "FRONTEND_README.md" ] && echo "✅" || echo "❌"

echo ""
echo "=========================================="
echo "✅ Setup verification complete!"
echo ""
echo "Ready to start? Run one of these:"
echo ""
echo "  1. Full Stack:     ./start.sh"
echo "  2. Frontend Only:  ./start-frontend.sh"
echo "  3. Backend Only:   ./start-backend.sh"
echo "  4. Manual Frontend: cd frontend && npm start"
echo ""
echo "Open browser at: http://localhost:3000"
echo ""

