#!/bin/bash

# Test script for Gemini API
# Usage: ./test_gemini_api.sh <API_KEY>
# or: GEMINI_API_KEY=your_key ./test_gemini_api.sh

# Get API key from argument or environment variable
if [ $# -eq 1 ]; then
    API_KEY="$1"
elif [ -n "$GEMINI_API_KEY" ]; then
    API_KEY="$GEMINI_API_KEY"
else
    echo "❌ Error: No API key provided"
    echo ""
    echo "Usage:"
    echo "  $0 <API_KEY>"
    echo "  GEMINI_API_KEY=your_key $0"
    echo ""
    echo "Example:"
    echo "  $0 AIzaSy..."
    echo "  export GEMINI_API_KEY=AIzaSy... && $0"
    exit 1
fi

echo "Testing Gemini API key..."
echo "API Key: ${API_KEY:0:20}..."

# Test the API with a simple request
echo "Sending test request to Gemini API..."

response=$(curl -s -w "\n%{http_code}" \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Say hello in exactly 5 words"
          }
        ]
      }
    ]
  }')

# Extract HTTP status code (last line)
http_code=$(echo "$response" | tail -n1)
# Extract response body (everything except last line)
body=$(echo "$response" | head -n -1)

echo "HTTP Status Code: $http_code"
echo "Response Body:"
echo "$body"

if [ "$http_code" = "200" ]; then
    echo "✅ API key is working correctly!"
else
    echo "❌ There was an issue with the API request."
    echo "Check your API key and try again."
fi
