#!/bin/bash

# Quick test of the API

set -e

echo "🧪 Quick API Test..."

cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

# Start server in background
echo "Starting API server..."
python src/main.py &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ API is healthy!"
else
    echo "❌ API health check failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test root endpoint
echo "Testing root endpoint..."
if curl -s http://localhost:8000/ | grep -q "AI Summarizer API"; then
    echo "✅ Root endpoint working!"
else
    echo "❌ Root endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Kill server
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null

echo ""
echo "🎉 All tests passed!"
echo "🚀 API is ready for production deployment."