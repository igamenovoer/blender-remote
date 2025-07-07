import bpy
import os
import asyncio


# Global server instance (set by main __init__.py)
global_server = None


# Cleanup handler for Blender exit
@bpy.app.handlers.persistent
def cleanup_on_exit(dummy=None):
    """Cleanup handler called when Blender is closing"""
    import blender_auto_mcp
    print("Blender is closing, cleaning up Auto MCP server...")
    if blender_auto_mcp.global_server:
        blender_auto_mcp.global_server.stop()
        blender_auto_mcp.global_server = None


# Cleanup handler for save/load events to ensure server survives file operations
@bpy.app.handlers.persistent  
def ensure_server_after_load(dummy):
    """Ensure server state is consistent after file load"""
    import blender_auto_mcp
    if blender_auto_mcp.global_server and blender_auto_mcp.global_server.running:
        # Update scene properties to reflect server state
        try:
            if hasattr(bpy.context.scene, 'blender_auto_mcp_server_running'):
                bpy.context.scene.blender_auto_mcp_server_running = True
        except:
            pass


def load_environment_config():
    """Load configuration from environment variables"""
    config = {}
    
    # Get port from environment variable
    port_env = os.getenv('BLENDER_AUTO_MCP_SERVICE_PORT')
    if port_env:
        try:
            config['port'] = int(port_env)
        except ValueError:
            print(f"Invalid port in BLENDER_AUTO_MCP_SERVICE_PORT: {port_env}")
            config['port'] = 9876
    else:
        config['port'] = 9876
    
    # Get auto-start setting
    start_now_env = os.getenv('BLENDER_AUTO_MCP_START_NOW', '0')
    config['start_now'] = start_now_env.lower() in ('1', 'true', 'yes', 'on')
    
    return config


def auto_start_server():
    """Auto-start server based on environment configuration"""
    from .server import BlenderAutoMCPServer
    import blender_auto_mcp
    
    config = load_environment_config()
    
    if config['start_now']:
        print(f"Auto-starting Blender Auto MCP server on port {config['port']}")
        try:
            blender_auto_mcp.global_server = BlenderAutoMCPServer(port=config['port'])
            success = blender_auto_mcp.global_server.start()
            if not success:
                print("Auto-start failed - server could not be started")
                blender_auto_mcp.global_server = None
                return
            
            # In background mode, start the asyncio keep-alive loop in main thread
            if bpy.app.background:
                print("Auto-start: Starting asyncio background keep-alive loop")
                
                async def background_main():
                    """Main asyncio function to keep Blender alive in background"""
                    print("Background asyncio main started")
                    try:
                        # Wait until shutdown is signaled
                        await blender_auto_mcp.global_server.shutdown_event.wait()
                        print("Background asyncio main: shutdown event received")
                    except Exception as e:
                        print(f"Error in background asyncio main: {e}")
                
                try:
                    # Run the asyncio event loop in the main thread - this will block
                    # and prevent Blender from exiting until the shutdown event is set
                    print("Starting asyncio.run() to block main thread...")
                    asyncio.run(background_main())
                    print("Asyncio.run() completed, Blender will now exit")
                except Exception as e:
                    print(f"Error in asyncio.run(): {e}")
        except Exception as e:
            print(f"Failed to auto-start Blender Auto MCP server: {e}")
            blender_auto_mcp.global_server = None
            return
        
        # Update scene properties after a delay when context is available
        def update_scene_properties():
            try:
                # Check if context is available and server is still running
                if (hasattr(bpy.context, 'scene') and bpy.context.scene and 
                    blender_auto_mcp.global_server and blender_auto_mcp.global_server.running):
                    scene = bpy.context.scene
                    if hasattr(scene, 'blender_auto_mcp_port'):
                        scene.blender_auto_mcp_port = config['port']
                    if hasattr(scene, 'blender_auto_mcp_server_running'):
                        scene.blender_auto_mcp_server_running = True
                    print("Scene properties updated successfully")
                    return None  # Stop the timer
                elif blender_auto_mcp.global_server and not blender_auto_mcp.global_server.running:
                    # Server stopped, don't update properties
                    print("Server stopped before scene properties could be updated")
                    return None  # Stop the timer
                else:
                    return 0.1  # Try again in 0.1 seconds
            except Exception as e:
                print(f"Error updating scene properties: {e}")
                return None  # Stop the timer on error
        
        # Register timer to update scene properties when context is available
        bpy.app.timers.register(update_scene_properties, first_interval=0.1)


def register_handlers():
    """Register event handlers"""
    # Add cleanup handlers
    bpy.app.handlers.save_pre.append(cleanup_on_exit)
    bpy.app.handlers.load_post.append(ensure_server_after_load)


def unregister_handlers():
    """Unregister event handlers"""
    # Remove cleanup handlers
    if cleanup_on_exit in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(cleanup_on_exit)
    if ensure_server_after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ensure_server_after_load)