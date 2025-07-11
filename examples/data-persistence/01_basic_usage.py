#!/usr/bin/env python3
"""
Basic Data Persistence Example

Shows simple storage and retrieval of data in Blender session.
"""

import json
import socket
import sys


def send_command(command_type, params=None):
    """Send command to BLD Remote MCP service."""
    if params is None:
        params = {}
    
    command = {"type": command_type, "params": params}
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 6688))
        sock.send(json.dumps(command).encode())
        response = json.loads(sock.recv(4096).decode())
        return response
    finally:
        sock.close()


def main():
    print("🚀 Data Persistence Basic Usage Example")
    print("=" * 50)
    
    try:
        # 1. Store simple data
        print("📝 Storing user preferences...")
        response = send_command("put_persist_data", {
            "key": "user_prefs",
            "data": {
                "render_quality": "high",
                "auto_save": True,
                "units": "metric"
            }
        })
        print(f"   Result: {response.get('status')}")
        
        # 2. Store numerical data
        print("📊 Storing calculation results...")
        response = send_command("put_persist_data", {
            "key": "mesh_stats",
            "data": {
                "total_vertices": 8,
                "total_faces": 6,
                "volume": 1.0
            }
        })
        print(f"   Result: {response.get('status')}")
        
        # 3. Retrieve data
        print("📖 Retrieving user preferences...")
        response = send_command("get_persist_data", {
            "key": "user_prefs"
        })
        if response.get('status') == 'success':
            data = response['result']['data']
            print(f"   Render quality: {data['render_quality']}")
            print(f"   Auto save: {data['auto_save']}")
            print(f"   Units: {data['units']}")
        
        # 4. Get non-existent data with default
        print("🔍 Getting non-existent data...")
        response = send_command("get_persist_data", {
            "key": "missing_key",
            "default": "not found"
        })
        if response.get('status') == 'success':
            data = response['result']['data']
            found = response['result']['found']
            print(f"   Data: {data} (found: {found})")
        
        # 5. Remove data
        print("🗑️  Removing mesh stats...")
        response = send_command("remove_persist_data", {
            "key": "mesh_stats"
        })
        if response.get('status') == 'success':
            removed = response['result']['removed']
            print(f"   Removed: {removed}")
        
        # 6. Verify removal
        print("✅ Verifying removal...")
        response = send_command("get_persist_data", {
            "key": "mesh_stats"
        })
        if response.get('status') == 'success':
            found = response['result']['found']
            print(f"   Data still exists: {found}")
        
        print("\n✅ Basic usage example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())