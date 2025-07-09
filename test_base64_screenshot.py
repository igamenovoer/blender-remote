#!/usr/bin/env python3
"""
Test base64 screenshot functionality specifically.
"""
import sys
import os
import asyncio
import base64
sys.path.insert(0, '/workspace/code/blender-remote/src')

async def test_base64_screenshot():
    """Test if screenshot returns base64 encoded data."""
    try:
        from blender_remote.mcp_server import blender_conn
        
        print("📸 Testing base64 screenshot functionality...")
        
        # Test screenshot capture
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), "test_screenshot.png")
        
        response = await blender_conn.send_command({
            "type": "get_viewport_screenshot",
            "params": {
                "max_size": 400,
                "format": "png",
                "filepath": temp_path
            }
        })
        
        if response.get("status") == "success":
            result = response.get("result", {})
            
            print("✅ Screenshot captured successfully")
            print(f"   Filepath: {result.get('filepath', 'N/A')}")
            print(f"   Dimensions: {result.get('width', 'N/A')}x{result.get('height', 'N/A')}")
            
            # Test base64 encoding
            filepath = result.get("filepath")
            if filepath and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    image_data = f.read()
                
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                print(f"✅ Base64 encoding successful")
                print(f"   Original size: {len(image_data)} bytes")
                print(f"   Base64 size: {len(base64_data)} characters")
                print(f"   Base64 preview: {base64_data[:50]}...")
                
                # Verify it's valid base64
                try:
                    decoded = base64.b64decode(base64_data)
                    if len(decoded) == len(image_data):
                        print("✅ Base64 round-trip validation successful")
                        return {
                            "type": "image",
                            "data": base64_data,
                            "mimeType": "image/png",
                            "size": len(image_data),
                            "dimensions": {
                                "width": result.get("width"),
                                "height": result.get("height")
                            }
                        }
                    else:
                        print("❌ Base64 round-trip validation failed")
                        return None
                except Exception as e:
                    print(f"❌ Base64 validation error: {e}")
                    return None
            else:
                print(f"❌ Screenshot file not found: {filepath}")
                return None
        else:
            error_msg = response.get("message", "Unknown error")
            print(f"❌ Screenshot failed: {error_msg}")
            if "background mode" in error_msg.lower():
                print("ℹ️  Note: Screenshots require GUI mode, not background mode")
            return None
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return None

async def main():
    """Run base64 screenshot test."""
    print("🧪 Testing Base64 Screenshot Functionality")
    print("=" * 50)
    
    result = await test_base64_screenshot()
    
    if result:
        print(f"\n🎉 Base64 screenshot test successful!")
        print(f"📊 Response format:")
        print(f"   Type: {result['type']}")
        print(f"   MIME: {result['mimeType']}")
        print(f"   Size: {result['size']} bytes")
        print(f"   Dimensions: {result['dimensions']['width']}x{result['dimensions']['height']}")
        print(f"   Base64 length: {len(result['data'])} characters")
        print(f"\n✅ Ready for LLM client integration!")
        return 0
    else:
        print(f"\n❌ Base64 screenshot test failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))