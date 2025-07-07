#!/usr/bin/env python3
"""
Code Execution Example

This example demonstrates executing Python code remotely in Blender
using the BLD Remote MCP background service.

Prerequisites:
- BLD Remote MCP service running (use start_service.py)
- Blender with bpy module available

Usage:
    python3 02_code_execution.py
    python3 02_code_execution.py --port 9999 --interactive
"""

import sys
import os
import argparse
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import blender_connection, check_service_health, validate_response

def basic_code_execution(port: int = 6688):
    """
    Demonstrate basic Python code execution in Blender.
    
    Args:
        port: Service port number
    """
    print(f"🐍 Testing code execution on BLD Remote MCP service (port {port})")
    print("=" * 60)
    
    # Check service availability
    health = check_service_health(port=port)
    if not health["responsive"]:
        print("❌ Service not available. Start with: python3 start_service.py")
        return False
    
    try:
        with blender_connection(port=port) as client:
            
            print("1. Basic Python expressions...")
            
            # Simple print statement
            response = client.execute_code(
                "print('Hello from Blender!')", 
                "Simple print test"
            )
            print(f"   Print response: {response.get('message', 'No message')}")
            
            # Basic arithmetic
            response = client.execute_code(
                "result = 2 + 2; print(f'2 + 2 = {result}')",
                "Arithmetic test"
            )
            print(f"   Arithmetic response: {response.get('message', 'No message')}")
            
            print("\\n2. Blender API access...")
            
            # Get Blender version
            response = client.execute_code(
                "import bpy; print(f'Blender version: {bpy.app.version_string}')",
                "Version check"
            )
            print(f"   Version response: {response.get('message', 'No message')}")
            
            # Count objects in scene
            response = client.execute_code(
                "import bpy; print(f'Objects in scene: {len(bpy.data.objects)}')",
                "Object count"
            )
            print(f"   Object count response: {response.get('message', 'No message')}")
            
            print("\\n3. Scene information...")
            
            # Get scene name and details
            code = '''
import bpy
scene = bpy.context.scene
print(f"Scene name: {scene.name}")
print(f"Frame current: {scene.frame_current}")
print(f"Frame start: {scene.frame_start}")
print(f"Frame end: {scene.frame_end}")
            '''
            response = client.execute_code(code, "Scene info")
            print(f"   Scene info response: {response.get('message', 'No message')}")
            
            print("\\n4. List all objects...")
            
            # List all objects with types
            code = '''
import bpy
print("Objects in scene:")
for obj in bpy.data.objects:
    print(f"  - {obj.name} ({obj.type})")
if not bpy.data.objects:
    print("  (No objects in scene)")
            '''
            response = client.execute_code(code, "List objects")
            print(f"   Objects list response: {response.get('message', 'No message')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Code execution failed: {e}")
        return False

def advanced_code_execution(port: int = 6688):
    """
    Demonstrate more advanced code execution patterns.
    
    Args:
        port: Service port number
    """
    print("\\n🚀 Advanced code execution examples...")
    print("=" * 60)
    
    try:
        with blender_connection(port=port) as client:
            
            print("1. Multi-line script execution...")
            
            # Complex multi-line script
            script = '''
import bpy
import mathutils

# Function to create a simple scene
def setup_basic_scene():
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    # Add a cube
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "MCP_Cube"
    
    # Add a light
    bpy.ops.object.light_add(type='SUN', location=(4, 4, 10))
    light = bpy.context.active_object
    light.name = "MCP_Light"
    
    # Add a camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.name = "MCP_Camera"
    
    # Point camera at cube
    direction = mathutils.Vector((0, 0, 0)) - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    print(f"Created basic scene with {len(bpy.data.objects)} objects")
    return cube, light, camera

# Execute the function
cube, light, camera = setup_basic_scene()
print(f"Scene setup complete!")
print(f"Cube: {cube.name} at {cube.location}")
print(f"Light: {light.name} at {light.location}")
print(f"Camera: {camera.name} at {camera.location}")
            '''
            
            response = client.execute_code(script, "Scene setup script")
            print(f"   Script response: {response.get('message', 'No message')}")
            
            print("\\n2. Error handling in remote code...")
            
            # Intentional error to test error handling
            error_code = '''
try:
    # This will cause an error
    result = 1 / 0
except ZeroDivisionError as e:
    print(f"Caught expected error: {e}")
    print("Error handling working correctly!")
except Exception as e:
    print(f"Unexpected error: {e}")
            '''
            
            response = client.execute_code(error_code, "Error handling test")
            print(f"   Error handling response: {response.get('message', 'No message')}")
            
            print("\\n3. Working with Blender data...")
            
            # Access and modify Blender data
            data_code = '''
import bpy

# Work with materials
if "MCP_Material" not in bpy.data.materials:
    mat = bpy.data.materials.new(name="MCP_Material")
    mat.use_nodes = True
    print(f"Created material: {mat.name}")
else:
    mat = bpy.data.materials["MCP_Material"]
    print(f"Using existing material: {mat.name}")

# Apply material to cube if it exists
cube = bpy.data.objects.get("MCP_Cube")
if cube and cube.type == 'MESH':
    if not cube.data.materials:
        cube.data.materials.append(mat)
        print(f"Applied material to {cube.name}")
    else:
        print(f"Material already applied to {cube.name}")

# Count different data types
print(f"Scene statistics:")
print(f"  Objects: {len(bpy.data.objects)}")
print(f"  Materials: {len(bpy.data.materials)}")
print(f"  Meshes: {len(bpy.data.meshes)}")
print(f"  Lights: {len(bpy.data.lights)}")
print(f"  Cameras: {len(bpy.data.cameras)}")
            '''
            
            response = client.execute_code(data_code, "Data manipulation")
            print(f"   Data manipulation response: {response.get('message', 'No message')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Advanced code execution failed: {e}")
        return False

def interactive_code_execution(port: int = 6688):
    """
    Interactive code execution mode.
    
    Args:
        port: Service port number
    """
    print("\\n💬 Interactive code execution mode")
    print("=" * 60)
    print("Enter Python code to execute in Blender (or 'quit' to exit)")
    print("Multi-line code: end with a line containing only '---'")
    print()
    
    try:
        with blender_connection(port=port) as client:
            
            while True:
                try:
                    # Get user input
                    print(">>> ", end="")
                    line = input().strip()
                    
                    if line.lower() in ('quit', 'exit', 'q'):
                        break
                    
                    if not line:
                        continue
                    
                    # Handle multi-line input
                    if line == '---':
                        continue
                    
                    code_lines = [line]
                    
                    # Check if this might be multi-line code
                    if line.endswith(':') or line.endswith('\\\\'):
                        print("... (multi-line mode, end with '---' on its own line)")
                        while True:
                            print("... ", end="")
                            next_line = input()
                            if next_line.strip() == '---':
                                break
                            code_lines.append(next_line)
                    
                    # Execute the code
                    code = '\\n'.join(code_lines)
                    response = client.execute_code(code, "Interactive command")
                    
                    # Show response
                    if validate_response(response):
                        print(f"✓ {response.get('message', 'Executed successfully')}")
                    else:
                        print(f"❌ Error: {response.get('message', 'Unknown error')}")
                    
                    print()
                    
                except KeyboardInterrupt:
                    print("\\nUse 'quit' to exit")
                except EOFError:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            print("Interactive session ended")
            
    except Exception as e:
        print(f"❌ Interactive mode failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test code execution in BLD Remote MCP')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--basic-only', action='store_true',
                        help='Run only basic tests')
    parser.add_argument('--interactive', action='store_true',
                        help='Start interactive code execution mode')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Code Execution Example")
    print("=" * 50)
    
    # Run basic tests
    success = basic_code_execution(args.port)
    
    if success and not args.basic_only:
        # Run advanced tests
        success = advanced_code_execution(args.port)
    
    if success and args.interactive:
        # Start interactive mode
        interactive_code_execution(args.port)
    
    if success:
        print("\\n🎉 Code execution examples completed successfully!")
        if not args.interactive:
            print("\\nNext steps:")
            print("  • Try interactive mode: python3 02_code_execution.py --interactive")
            print("  • Try scene manipulation: python3 03_scene_manipulation.py")
    else:
        print("\\n❌ Code execution tests failed")
        print("\\nTroubleshooting:")
        print(f"  • Ensure service is running: python3 start_service.py --port {args.port}")
        print("  • Check Blender console for Python errors")
        print("  • Verify bpy module is available in Blender")
        
        sys.exit(1)

if __name__ == '__main__':
    main()