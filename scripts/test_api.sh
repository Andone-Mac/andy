#!/bin/bash

# Test script for AI Summarizer API

set -e

echo "🧪 Testing AI Summarizer API..."

# Wait for API to start (if not already running)
sleep 2

# Base URL
BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$BASE_URL/health" | jq -r '.status' | grep -q "healthy" && echo "✅ Health check passed" || echo "❌ Health check failed"

# Test 2: Root endpoint
echo "2. Testing root endpoint..."
curl -s "$BASE_URL/" | jq -r '.service' | grep -q "AI Summarizer API" && echo "✅ Root endpoint passed" || echo "❌ Root endpoint failed"

# Test 3: Create API key
echo "3. Testing API key creation..."
KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/keys" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}')

API_KEY=$(echo "$KEY_RESPONSE" | jq -r '.api_key')
if [ "$API_KEY" != "null" ] && [ ! -z "$API_KEY" ]; then
    echo "✅ API key created: ${API_KEY:0:20}..."
else
    echo "❌ API key creation failed"
    echo "Response: $KEY_RESPONSE"
fi

# Test 4: Summarize with demo key (if available)
echo "4. Testing summarization with demo key..."
DEMO_INFO=$(curl -s "$BASE_URL/" | jq -r '.demo_api_key')
if [ "$DEMO_INFO" != "null" ]; then
    DEMO_KEY="$DEMO_INFO"
    echo "   Using demo key: ${DEMO_KEY:0:20}..."
    
    SUMMARY_RESPONSE=$(curl -s -X POST "$BASE_URL/summarize" \
      -H "Authorization: Bearer $DEMO_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "text": "Artificial intelligence is transforming the world. Machine learning algorithms can now recognize patterns in data that humans cannot see. Deep learning has revolutionized computer vision and natural language processing. AI assistants help people with daily tasks, from scheduling to content creation. The future of AI holds both promise and challenges that we must navigate carefully.",
        "max_length": 50,
        "language": "en"
      }')
    
    ERROR=$(echo "$SUMMARY_RESPONSE" | jq -r '.detail // empty')
    if [ -z "$ERROR" ]; then
        echo "✅ Summarization test passed"
        echo "   Summary: $(echo "$SUMMARY_RESPONSE" | jq -r '.summary' | cut -c 1-50)..."
    else
        echo "❌ Summarization failed: $ERROR"
    fi
else
    echo "⚠️  No demo key found in root endpoint"
fi

# Test 5: Stats endpoint
echo "5. Testing stats endpoint..."
if [ ! -z "$API_KEY" ]; then
    STATS_RESPONSE=$(curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/stats")
    ERROR=$(echo "$STATS_RESPONSE" | jq -r '.detail // empty')
    if [ -z "$ERROR" ]; then
        echo "✅ Stats endpoint passed"
    else
        echo "❌ Stats endpoint failed: $ERROR"
    fi
else
    echo "⚠️  Skipping stats test (no API key)"
fi

echo ""
echo "🎉 API testing complete!"
echo ""
echo "💰 Next steps for revenue generation:"
echo "1. Update .env with live Stripe keys"
echo "2. Set up Stripe webhook in dashboard"
echo "3. Deploy to production (Render, Railway, etc.)"
echo "4. Create landing page and marketing"
echo "5. Start acquiring paying customers!"