import socket
import json
import logging

def test_bld_remote_mcp_tcp(host='127.0.0.1', port=6688):
    """Test BLD_Remote_MCP TCP service directly"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        logger.info(f"Connected to {host}:{port}")
        
        # Test basic connection
        command = {"message": "connection test", "code": "print('Direct TCP connection successful')"}
        sock.sendall(json.dumps(command).encode('utf-8'))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        logger.info(f"Response: {response}")
        sock.close()
        return response
    except Exception as e:
        logger.error(f"TCP test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_bld_remote_mcp_tcp()
    print(json.dumps(result, indent=2))