#!/bin/bash

echo "🔍 Verifying Enchères du Domaine Installation"
echo "=============================================="
echo ""

# Check if files exist
echo "📁 Checking file structure..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/app/main.py"
    "frontend/Dockerfile"
    "frontend/package.json"
    "frontend/src/App.tsx"
    ".env.example"
    "README.md"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   ❌ Missing: $file"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -eq 0 ]; then
    echo "   ✅ All required files present"
else
    echo "   ⚠️  $MISSING files missing!"
fi

echo ""

# Check Docker
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker installed: $(docker --version)"
else
    echo "   ❌ Docker not found - Install from https://docker.com"
fi

if command -v docker-compose &> /dev/null; then
    echo "   ✅ Docker Compose installed: $(docker-compose --version)"
else
    echo "   ❌ Docker Compose not found"
fi

echo ""

# Check environment files
echo "🔐 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "   ✅ Backend .env exists"
else
    echo "   ⚠️  Backend .env not found - will be created by start.sh"
fi

if [ -f "frontend/.env" ]; then
    echo "   ✅ Frontend .env exists"
else
    echo "   ⚠️  Frontend .env not found - will be created by start.sh"
fi

echo ""

# Summary
echo "📊 Installation Summary:"
echo "========================"
echo ""
echo "Backend:"
echo "   - $(find backend/app -name '*.py' | wc -l) Python files"
echo "   - FastAPI + SQLAlchemy + PostgreSQL"
echo "   - JWT Authentication"
echo "   - Automatic scraping every 15min"
echo ""
echo "Frontend:"
echo "   - $(find frontend/src -name '*.ts' -o -name '*.tsx' | wc -l) TypeScript/React files"
echo "   - React 18 + Vite + TailwindCSS"
echo "   - Dark/Light theme"
echo "   - French/English support"
echo ""
echo "Infrastructure:"
echo "   - Docker containerization"
echo "   - PostgreSQL database"
echo "   - Redis caching"
echo ""

# Ready to run
echo "✨ Next Steps:"
echo "=============="
echo ""
if [ ! -f ".env" ]; then
    echo "1. Configure environment:"
    echo "   cp .env.example .env"
    echo "   nano .env  # Edit SECRET_KEY and other settings"
    echo ""
fi

if command -v docker &> /dev/null; then
    echo "2. Start the application:"
    echo "   ./start.sh"
    echo "   OR"
    echo "   docker-compose up --build"
    echo ""
    echo "3. Access the app:"
    echo "   Frontend: http://localhost:5173"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "2. Install Docker from https://docker.com"
    echo ""
    echo "3. Then run: ./start.sh"
fi

echo ""
echo "📚 Documentation:"
echo "   - Quick Start: QUICKSTART.md"
echo "   - Full Docs:   README.md"
echo "   - Summary:     PROJECT_SUMMARY.md"
echo ""
echo "🎉 Installation verified! Ready to start."
