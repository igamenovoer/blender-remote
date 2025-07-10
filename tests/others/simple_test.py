#!/usr/bin/env python3
import socket
import time

print("Testing port availability...")


# Test if ports are available
def test_port(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except:
        return False


port_6688 = test_port(6688)
port_9876 = test_port(9876)

print(f"Port 6688 (BLD_Remote_MCP): {'CONNECTED' if port_6688 else 'NOT AVAILABLE'}")
print(f"Port 9876 (BlenderAutoMCP): {'CONNECTED' if port_9876 else 'NOT AVAILABLE'}")

if port_6688 or port_9876:
    print("At least one service is running!")
else:
    print("No services detected. Need to start Blender with MCP services.")
