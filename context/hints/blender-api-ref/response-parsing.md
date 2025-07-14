# Response Parsing and I/O Handling - blender-remote Patterns

## BLD Remote MCP Response Structure

**From our debugging - actual response format:**
```json
{
  "status": "success",
  "result": {
    "executed": true,
    "result": "OBJECT_NAME:TestCube\n",     // ← Print output here
    "output": {
      "stdout": "OBJECT_NAME:TestCube\n",   // ← Also here  
      "stderr": ""
    }
  }
}
```

## Response Field Access Patterns

**❌ WRONG (causes empty results):**
```python
# This field doesn't exist in the response
response.get("result", {}).get("message", "")
```

**✅ RIGHT (working pattern from our fix):**
```python
def parse_execute_response(response):
    """Parse response from execute_code command."""
    result_data = response.get("result", {})
    
    # Try to get output from 'result' field first
    output = result_data.get("result", "")
    
    # Fallback to 'output.stdout' if 'result' is empty
    if not output:
        output = result_data.get("output", {}).get("stdout", "")
    
    return output
```

## String Parsing Patterns

**Object name extraction (from our fixes):**
```python
def extract_object_name(result_string):
    """Extract object name from command result."""
    for line in result_string.split("\n"):
        if line.startswith("OBJECT_NAME:"):
            return line[12:]  # Remove "OBJECT_NAME:" prefix
        elif line.startswith("OBJECT_ERROR:"):
            error_msg = line[13:]
            print(f"Object creation error: {error_msg}")
            return ""
    
    # No object name found
    if not result_string.strip():
        print("Warning: No output received from command")
    else:
        print(f"Warning: Object name not found in: {result_string[:200]}...")
    
    return ""
```

**Boolean result parsing:**
```python
def parse_boolean_result(result_string, success_marker):
    """Parse boolean success/failure from result."""
    return success_marker in result_string

# Example usage
clear_success = parse_boolean_result(result, "CLEAR_SUCCESS:True")
delete_success = parse_boolean_result(result, "DELETE_SUCCESS:True")
```

**JSON data extraction:**
```python
def extract_json_data(result_string, prefix):
    """Extract JSON data from prefixed line."""
    for line in result_string.split("\n"):
        if line.startswith(prefix):
            try:
                import ast
                json_str = line[len(prefix):]
                return ast.literal_eval(json_str)
            except (ValueError, SyntaxError) as e:
                print(f"JSON parsing error: {e}")
                return None
    return None

# Example usage
objects_data = extract_json_data(result, "OBJECTS_JSON:")
update_results = extract_json_data(result, "UPDATE_RESULTS:")
```

## Print-Based Communication Patterns

**Structured output for remote parsing:**
```python
def structured_print_pattern():
    """Pattern for structured print output."""
    
    # Object creation result
    print(f"OBJECT_NAME:{obj.name}")
    
    # Error reporting
    print(f"OBJECT_ERROR:{error_message}")
    
    # Boolean success
    print(f"OPERATION_SUCCESS:{success}")
    
    # JSON data transfer
    print(f"DATA_JSON:{json.dumps(data)}")
    
    # Multi-line data with markers
    print("DATA_START")
    for item in data:
        print(item)
    print("DATA_END")
```

**Error information patterns:**
```python
def error_reporting_pattern():
    """Pattern for comprehensive error reporting."""
    
    try:
        # Perform operation
        result = perform_blender_operation()
        print(f"SUCCESS:{result}")
        
    except RuntimeError as e:
        print(f"RUNTIME_ERROR:{str(e)}")
        
    except Exception as e:
        print(f"GENERAL_ERROR:{str(e)}")
        
    # Always provide some status
    print(f"OPERATION_COMPLETE:{'success' if success else 'failed'}")
```

## Base64 Data Transfer

**Pattern for binary data (GLB files):**
```python
import base64

def base64_transfer_pattern(binary_data, data_type="GLB"):
    """Pattern for transferring binary data as base64."""
    
    # Encode to base64
    base64_str = base64.b64encode(binary_data).decode('utf-8')
    file_size = len(binary_data)
    
    # Structured output with size verification
    print(f"EXPORT_SUCCESS:{file_size}")
    print(f"{data_type}_BASE64_START")
    print(base64_str)
    print(f"{data_type}_BASE64_END")
    
    return base64_str

def parse_base64_response(result_string, data_type="GLB"):
    """Parse base64 data from response."""
    start_marker = f"{data_type}_BASE64_START"
    end_marker = f"{data_type}_BASE64_END"
    
    lines = result_string.split("\n")
    in_base64_section = False
    base64_data = ""
    file_size = 0
    
    for line in lines:
        if line.startswith("EXPORT_SUCCESS:"):
            file_size = int(line[15:])
        elif line == start_marker:
            in_base64_section = True
        elif line == end_marker:
            in_base64_section = False
        elif in_base64_section:
            base64_data += line
    
    if base64_data:
        try:
            binary_data = base64.b64decode(base64_data)
            if len(binary_data) == file_size:
                return binary_data
            else:
                raise ValueError(f"Size mismatch: expected {file_size}, got {len(binary_data)}")
        except Exception as e:
            raise ValueError(f"Base64 decode error: {e}")
    
    raise ValueError("No base64 data found in response")
```

## Robust Parsing with Error Recovery

**Multi-format parsing:**
```python
def robust_result_parser(result_string, expected_patterns):
    """Parse result with multiple pattern attempts."""
    
    results = {}
    
    for pattern_name, pattern_prefix in expected_patterns.items():
        for line in result_string.split("\n"):
            if line.startswith(pattern_prefix):
                value = line[len(pattern_prefix):]
                results[pattern_name] = value
                break
        else:
            results[pattern_name] = None
    
    return results

# Example usage
patterns = {
    'object_name': 'OBJECT_NAME:',
    'success': 'SUCCESS:',
    'error': 'ERROR:'
}

parsed = robust_result_parser(result, patterns)
if parsed['object_name']:
    return parsed['object_name']
elif parsed['error']:
    raise Exception(parsed['error'])
```

## Debugging and Logging

**I/O debugging pattern:**
```python
def debug_io_communication():
    """Debug I/O communication patterns."""
    
    print("=== I/O DEBUG START ===")
    print(f"Command: {command}")
    print(f"Parameters: {params}")
    print("--- Raw Response ---")
    print(repr(raw_response))
    print("--- Parsed Response ---")
    print(parsed_response)
    print("--- Field Analysis ---")
    
    if 'result' in parsed_response:
        result_data = parsed_response['result']
        print(f"result.result: {result_data.get('result', 'NOT_FOUND')}")
        print(f"result.output.stdout: {result_data.get('output', {}).get('stdout', 'NOT_FOUND')}")
        print(f"result.message: {result_data.get('message', 'NOT_FOUND')}")
    
    print("=== I/O DEBUG END ===")
```

## Common I/O Error Patterns

**Empty result troubleshooting:**
```python
def diagnose_empty_result(response, result_string):
    """Diagnose why result is empty."""
    
    print("=== EMPTY RESULT DIAGNOSIS ===")
    
    # Check response structure
    if not response:
        print("ERROR: No response received")
        return
    
    if response.get('status') != 'success':
        print(f"ERROR: Response status: {response.get('status')}")
        print(f"ERROR: Message: {response.get('message', 'No message')}")
        return
    
    # Check result field structure
    result_data = response.get('result', {})
    if not result_data:
        print("ERROR: No 'result' field in response")
        return
    
    # Check available fields
    print(f"Available result fields: {list(result_data.keys())}")
    
    for field in ['result', 'output', 'message', 'executed']:
        value = result_data.get(field)
        print(f"result.{field}: {repr(value)}")
    
    # Check if it's a parsing issue
    if not result_string.strip():
        print("ERROR: Parsed result string is empty")
    else:
        print(f"Parsed result preview: {result_string[:100]}...")
```

## Notes for blender-remote Development

- **Field reliability**: Always use `response["result"]["result"]` for print output
- **Fallback strategy**: Check `output.stdout` as secondary source
- **Structured output**: Use consistent prefixes for parseable results
- **Error reporting**: Include diagnostic information in output
- **Binary transfer**: Use base64 with size verification for GLB data
- **Debugging**: Implement comprehensive I/O logging for troubleshooting
- **Validation**: Always validate parsed data before use