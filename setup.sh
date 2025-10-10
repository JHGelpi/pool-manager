#!/bin/bash

echo "🏊 Pool Manager - Setup Script"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit the .env file with your settings:"
    echo "   - Set DB_PASSWORD to a secure password"
    echo "   - Set SECRET_KEY (run: openssl rand -hex 32)"
    echo "   - Configure SMTP settings if you want email alerts"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if API is healthy
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ API failed to start. Check logs with: docker-compose logs api"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📍 Access your application:"
echo "   Frontend:  http://localhost:8000/static/index.html"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "🔐 Default login:"
echo "   Email:     admin@example.com"
echo "   Password:  admin123"
echo ""
echo "⚠️  Remember to change the default password!"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Shell access:     docker-compose exec api bash"
echo ""