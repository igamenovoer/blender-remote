# How to Interact with a FastMCP Server Using a Python Client for Testing

This guide demonstrates how to create a Python client to interact with a `fastmcp` server. This is a common pattern for testing your MCP server's functionality without needing a full LLM or IDE environment. We will cover setting up a basic server, writing a client script, and running them together.

## 1. The Core Components

You need two main pieces for this testing setup:

-   **A FastMCP Server**: The server that exposes tools and resources.
-   **A Python Client**: A script that uses the `fastmcp.Client` class to connect to your server and call its tools.

## 2. Creating a Simple FastMCP Server

First, let's create a simple `fastmcp` server to test against. This server will have one simple tool.

Save this code as `my_mcp_server.py`:

```python
# my_mcp_server.py
from fastmcp import FastMCP, Context
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a FastMCP server instance
mcp = FastMCP("MyTestServer", description="A simple server for testing.")

@mcp.tool()
def say_hello(name: str, ctx: Context) -> str:
    """A simple tool that returns a greeting."""
    logger.info(f"Tool 'say_hello' called with name: {name}")
    return f"Hello, {name}! This is the server speaking."

def main():
    """Main function to run the server."""
    logger.info("Starting MyTestServer...")
    # The run() method starts the server and listens for connections via stdio
    mcp.run()

if __name__ == "__main__":
    main()
```

This server has a single tool `say_hello` that takes a name and returns a greeting.

## 3. Writing the Python Client

Now, let's write a Python script that will act as a client to this server. The `fastmcp` library provides a `Client` class for this.

Save this code as `test_client.py`:

```python
# test_client.py
import asyncio
import subprocess
import os
from fastmcp.client import Client, ClientError
from fastmcp.transport.stdio import StdioClientTransport
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    """
    Starts the server as a subprocess and interacts with it using a client.
    """
    server_process = None
    try:
        # 1. Start the MCP server as a subprocess
        # We use sys.executable to ensure we're using the same Python interpreter
        python_executable = os.sys.executable
        cmd = [python_executable, "my_mcp_server.py"]
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        
        server_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE # Capture stderr for debugging
        )

        # Give the server a moment to start up
        await asyncio.sleep(1)

        # 2. Create a client transport
        # StdioClientTransport communicates with the server's standard input/output
        transport = StdioClientTransport(
            process_stdin=server_process.stdin,
            process_stdout=server_process.stdout
        )

        # 3. Create a client instance
        async with Client(transport=transport) as client:
            logger.info("Client created. Connecting to server...")
            
            # 4. List available tools
            tools = await client.list_tools()
            logger.info(f"Available tools: {[tool.name for tool in tools]}")
            assert any(tool.name == "say_hello" for tool in tools)

            # 5. Call a tool
            logger.info("Calling the 'say_hello' tool...")
            try:
                result = await client.call_tool("say_hello", {"name": "World"})
                logger.info(f"Server response: {result}")
                assert result == "Hello, World! This is the server speaking."
                print("\n✅ Test Passed: Successfully called the tool and received the correct response.")
            except ClientError as e:
                logger.error(f"Error calling tool: {e}")
                print(f"\n❌ Test Failed: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"\n❌ Test Failed: {e}")

    finally:
        # 6. Clean up the server process
        if server_process:
            logger.info("Terminating server process...")
            server_process.terminate()
            stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, server_process.communicate
            )
            if stdout:
                logger.info(f"Server stdout:\n{stdout.decode()}")
            if stderr:
                logger.error(f"Server stderr:\n{stderr.decode()}")
            logger.info("Server process terminated.")

if __name__ == "__main__":
    asyncio.run(run_test())

```

### Key Concepts in the Client:

-   **`subprocess.Popen`**: We start the MCP server in a separate process so the client can connect to it.
-   **`StdioClientTransport`**: This is the transport layer that handles communication over the server's `stdin` and `stdout`. This is the standard for `fastmcp` servers started with `mcp.run()`.
-   **`Client`**: The main class for interacting with the MCP server. It's used as an async context manager (`async with`).
-   **`client.list_tools()`**: Fetches the list of available tools from the server.
-   **`client.call_tool()`**: Executes a specific tool on the server with given parameters.
-   **`ClientError`**: A specific exception raised if the tool call fails on the server side.

## 4. Running the Test

To run this test, you need to have both files (`my_mcp_server.py` and `test_client.py`) in the same directory. You'll also need to have `fastmcp` installed.

```bash
# Install fastmcp if you haven't already
pip install fastmcp

# Run the client script
python test_client.py
```

### Expected Output:

You should see output similar to this:

```
INFO:__main__:Starting server with command: /path/to/your/python my_mcp_server.py
INFO:__main__:Client created. Connecting to server...
INFO:my_mcp_server:Starting MyTestServer...
INFO:__main__:Available tools: ['say_hello']
INFO:__main__:Calling the 'say_hello' tool...
INFO:my_mcp_server:Tool 'say_hello' called with name: World
INFO:__main__:Server response: Hello, World! This is the server speaking.

✅ Test Passed: Successfully called the tool and received the correct response.
INFO:__main__:Terminating server process...
INFO:__main__:Server process terminated.
```

## Conclusion

This guide provides a basic but powerful pattern for testing your `fastmcp` servers. By creating a client that runs your server as a subprocess, you can programmatically test your tools and resources, making it a great addition to a continuous integration (CI) pipeline or for local development testing.
