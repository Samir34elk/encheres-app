#!/bin/bash

echo "🚀 Starting Enchères du Domaine Application"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "✅ Created .env - Please edit it with your settings"
fi

if [ ! -f frontend/.env ]; then
    echo "⚠️  frontend/.env file not found. Creating from example..."
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
fi

# Build and start containers
echo ""
echo "📦 Building Docker containers..."
docker-compose build

echo ""
echo "🔄 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Access points:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop application:"
echo "   docker-compose down"
echo ""
echo "🗑️  Remove all data:"
echo "   docker-compose down -v"
echo ""
