# API Tests

This directory contains test scripts for external API integrations.

## Test Scripts

### **`test_gemini_api.sh`**
- **Purpose**: Test Gemini API connectivity and authentication
- **Type**: External API integration test
- **Security**: Uses command line argument or environment variable for API key

**Usage Options**:
```bash
# Option 1: Command line argument
bash tests/api-tests/test_gemini_api.sh "your_api_key_here"

# Option 2: Environment variable
export GEMINI_API_KEY="your_api_key_here"
bash tests/api-tests/test_gemini_api.sh

# Option 3: One-time environment variable
GEMINI_API_KEY="your_api_key_here" bash tests/api-tests/test_gemini_api.sh
```

**✅ Security Features**:
- No hardcoded API keys in source code
- Supports both CLI argument and environment variable input
- Displays only first 20 characters of API key for verification
- Clear usage instructions and error messages

## Usage

```bash
# Run Gemini API test with API key as argument
cd /workspace/code/blender-remote
bash tests/api-tests/test_gemini_api.sh "your_api_key_here"

# Or with environment variable
export GEMINI_API_KEY="your_api_key_here"
bash tests/api-tests/test_gemini_api.sh
```

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables for sensitive data**
3. **Rotate API keys regularly**
4. **Review access permissions**

## Integration

These tests validate external API integrations that may be used by:
- LLM-based features
- Cloud service integrations
- Third-party API connectivity