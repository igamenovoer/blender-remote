# MCP Implementation Guide

## Essential Protocol Information

### Core Architecture
- **Protocol Base**: JSON-RPC 2.0
- **Message Types**: Requests (with ID), Responses (matching ID), Notifications (no ID)
- **Connection**: Stateful with capability negotiation

### Protocol Lifecycle
1. **Initialize**: Client sends `initialize` request with protocol version + capabilities
2. **Capability Negotiation**: Server responds with supported features  
3. **Operation**: Message exchange using negotiated capabilities
4. **Shutdown**: Clean termination via transport mechanism

### Message Structure
```typescript
// Request
{
  jsonrpc: "2.0";
  id: string | number;  // MUST NOT be null, MUST be unique per session
  method: string;
  params?: object;
}

// Response  
{
  jsonrpc: "2.0";
  id: string | number;  // Same as request
  result?: object;      // On success
  error?: {             // On failure
    code: number;
    message: string;
    data?: unknown;
  }
}

// Notification
{
  jsonrpc: "2.0";
  method: string;
  params?: object;
  // NO id field
}
```

### Transport Options

**stdio Transport** (Recommended for CLI tools):
```
- Client launches server as subprocess
- Communication via stdin/stdout
- Messages are newline-delimited JSON-RPC
- Server MAY log to stderr
```

**HTTP Transport**:
```
- Server runs independently
- Single endpoint supporting POST/GET
- Optional Server-Sent Events (SSE) for streaming
- 'MCP-Protocol-Version' header required
```

### Server Capabilities

**Core Features**:
- `tools`: Callable functions for LLM actions
- `resources`: Contextual data (files, API responses)  
- `prompts`: Interactive templates for users
- `logging`: Structured log emission
- `completions`: Argument autocompletion

**Sub-capabilities**:
- `listChanged`: Notifications when lists change
- `subscribe`: Resource change subscriptions

### Initialization Sequence

```json
// 1. Client sends initialize
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize", 
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    },
    "clientInfo": {
      "name": "ExampleClient",
      "version": "1.0.0"
    }
  }
}

// 2. Server responds
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true },
      "logging": {}
    },
    "serverInfo": {
      "name": "ExampleServer", 
      "version": "1.0.0"
    }
  }
}

// 3. Client sends initialized notification
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

## Tool Implementation Pattern

### Tool Registration
Tools are the primary way to expose functionality to LLMs.

```python
# Python FastMCP example
@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for a location.
    
    Args:
        location: City name or coordinates
    """
    # Implementation here
    return f"Weather for {location}: ..."
```

```typescript
// TypeScript example
server.tool(
  "get-weather",
  "Get weather for a location",
  {
    location: z.string().describe("City name or coordinates")
  },
  async ({ location }) => {
    // Implementation here
    return {
      content: [{ type: "text", text: `Weather for ${location}: ...` }]
    };
  }
);
```

### Tool Call Flow
```json
// Client calls tool
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "San Francisco"
    }
  }
}

// Server responds
{
  "jsonrpc": "2.0", 
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Weather for San Francisco: 72°F, sunny"
      }
    ]
  }
}
```

## Security Requirements

**Mandatory**:
- Input validation on all parameters
- Rate limiting on requests  
- Access control for sensitive operations
- User consent for tool execution

**HTTP-specific**:
- Origin header validation
- Localhost binding for local servers
- Proper authentication

## Implementation Notes

### Key Requirements
- Use latest protocol version (draft, 2025-03-26)
- Handle version negotiation gracefully
- Implement proper error handling
- Support progress tracking for long operations
- Handle cancellation requests

### Tool Best Practices  
- Use descriptive names and descriptions
- Include proper JSON schemas for parameters
- Return structured content when possible
- Handle errors gracefully with meaningful messages
- Consider adding progress tracking for long operations

### Reference Implementation Structure
```python
# Minimal MCP server structure
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    # Tool implementation
    return result

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

## Finding Protocol Details

**Primary Sources**:
1. Query `context7` MCP server: `mcp__context7__resolve-library-id` + `mcp__context7__get-library-docs`
2. Check `/workspace/code/blender-remote/context/summaries/` for saved protocol information
3. Reference specification at `/workspace/code/blender-remote/context/refcode/modelcontextprotocol/`

**Key Schema Location**: 
- TypeScript: `schema/draft/schema.ts` (source of truth)
- JSON: `schema/draft/schema.json` (generated)