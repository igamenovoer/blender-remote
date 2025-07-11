# How to Use HTTPie for MCP Server Testing

This guide explains how to use `httpie`, a command-line HTTP client, to manually test and interact with a Model Context Protocol (MCP) server. This is useful for debugging your server, verifying tool implementations, and understanding the raw protocol.

## 1. Core Concepts

The Model Context Protocol (MCP) is built on top of a simple JSON-based request/response model. While not strictly JSON-RPC, it shares the same core idea: you send a JSON object describing the action you want to perform, and you receive a JSON object with the result.

`httpie` is an excellent tool for this because it simplifies the process of sending structured JSON data and provides colorized, formatted output of the response.

## 2. The MCP Request Format

An MCP request is a JSON object that specifies the tool to be called and the arguments to pass to it.

**Basic Structure:**
```json
{
    "tool_name": "name_of_the_tool",
    "arguments": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

## 3. Sending Raw JSON with HTTPie

The most effective way to send a pre-formatted JSON request body with `httpie` is to pipe it into the command using standard input. This gives you full control over the JSON structure, which is perfect for testing complex or nested MCP `arguments`.

The command follows this pattern:

```bash
echo '[JSON_PAYLOAD]' | http [METHOD] [URL] '[HEADER:VALUE]'
```

-   **`echo '[JSON_PAYLOAD]'`**: This command prints your JSON string to standard output.
-   **`|` (Pipe)**: This redirects the output of the `echo` command to the standard input of the `http` command.
-   **`http`**: The HTTPie executable.
-   **`[METHOD]`**: The HTTP method, which is typically `POST` for MCP tool calls.
-   **`[URL]`**: The URL where your MCP server is listening.
-   **`'[HEADER:VALUE]'`**: Any necessary HTTP headers, such as `Content-Type`.

## 4. Practical Example: Testing the `blender-remote` Server

Let's test the `execute_blender_code` tool provided by the `blender-remote` MCP server.

### Step 1: Ensure the Server is Running

First, make sure your `blender-remote` MCP server is running and listening on the correct port (e.g., `http://127.0.0.1:8000`).

You can start it with:
```bash
uvx blender-remote server --port 8000
```

### Step 2: Construct the JSON Payload

We want to call the `execute_blender_code` tool with a simple Python script as an argument.

**JSON Payload:**
```json
{
    "tool_name": "execute_blender_code",
    "arguments": {
        "code": "import bpy; print(f'Active scene: {bpy.context.scene.name}')"
    }
}
```

### Step 3: Execute the HTTPie Command

Now, we'll pipe this JSON payload into `httpie`.

```bash
echo '{ "tool_name": "execute_blender_code", "arguments": { "code": "import bpy; print(f'Active scene: {bpy.context.scene.name}')" } }' | http POST http://127.0.0.1:8000 Content-Type:application/json
```

**Command Breakdown:**
-   `echo '{...}'`: The JSON payload, enclosed in single quotes to protect the double quotes inside.
-   `|`: The pipe.
-   `http POST`: We are making a POST request.
-   `http://127.0.0.1:8000`: The address of our local MCP server.
-   `Content-Type:application/json`: This header tells the server that we are sending a JSON body.

### Step 4: Analyze the Response

If the command is successful, `httpie` will display the server's response, nicely formatted and colorized.

**Expected Server Response:**
```json
{
    "status": "success",
    "result": {
        "stdout": "Active scene: Scene\n",
        "stderr": "",
        "return_code": 0
    },
    "message": "Code executed successfully"
}
```

## 5. Specific Steps for `fastmcp` Servers

While the method above works for any MCP server that accepts raw HTTP POST requests, `fastmcp` servers often run using a specific command-line interface. To test a `fastmcp` server with `httpie`, you must run it with an HTTP-based transport like `sse`.

### Step 1: Run Your `fastmcp` Server with SSE Transport

Instead of using the default `stdio` transport, start your `fastmcp` server and explicitly tell it to use the `sse` (Server-Sent Events) transport, which works over HTTP.

```bash
fastmcp run your_server_script.py:mcp --transport sse --port 8080
```

- **`your_server_script.py:mcp`**: Path to your Python file and the `FastMCP` instance variable within it.
- **`--transport sse`**: This is the key part. It tells `fastmcp` to listen for HTTP connections.
- **`--port 8080`**: The port to listen on.

### Step 2: Use HTTPie to Send the Request

The `httpie` command remains the same as in the general example, but you'll point it to the port you specified. The default endpoint for tool calls in a `fastmcp` SSE server is `/tool`.

```bash
echo '{ "tool_name": "say_hello", "arguments": { "name": "FastMCP User" } }' | http POST http://127.0.0.1:8080/tool Content-Type:application/json
```

### Step 3: Analyze the `fastmcp` Response

A `fastmcp` server will wrap the tool's result in a standard MCP response structure.

**Expected Response from `fastmcp`:**
```json
{
    "result": "Hello, FastMCP User! This is the server speaking.",
    "session_id": "some-unique-id",
    "type": "tool_result"
}
```

This confirms that you can test any `fastmcp` server using `httpie` as long as you run it with an appropriate HTTP transport.

## Conclusion

Using `httpie` with piped raw JSON is a powerful and flexible way to test any MCP server. It allows you to craft precise requests, inspect raw server responses, and debug your tool implementations effectively without needing a full client application.
