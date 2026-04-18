#!/bin/bash

# Quick verification of API

set -e

cd "$(dirname "$0")/.."

echo "🧪 Verifying API..."

# Check if server is already running
if curl -s http://localhost:8000/health 2>/dev/null | grep -q healthy; then
    echo "✅ API is already running"
    exit 0
fi

# Start server in background
echo "Starting API server..."
venv/bin/python src/main.py &
SERVER_PID=$!

# Wait for server to start
for i in {1..10}; do
    if curl -s http://localhost:8000/health 2>/dev/null | grep -q healthy; then
        echo "✅ API started successfully"
        echo "🛑 Stopping test server..."
        kill $SERVER_PID 2>/dev/null
        wait $SERVER_PID 2>/dev/null
        exit 0
    fi
    sleep 1
done

echo "❌ API failed to start within 10 seconds"
kill $SERVER_PID 2>/dev/null
exit 1