#!/bin/bash

# Test script for Gemini API
API_KEY="AIzaSyBPd6aDW67XVxM8Qc1BmXp1ChKTDWxcqKY"

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
