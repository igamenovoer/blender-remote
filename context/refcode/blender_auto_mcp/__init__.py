import bpy

# Blender addon metadata
bl_info = {
    "name": "Blender Auto MCP",
    "author": "BlenderAutoMCP",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Blender Auto MCP",
    "description": "Auto-starting MCP server for Blender with environment variable configuration",
    "category": "Interface",
}

# Import all components from submodules
from .server import BlenderAutoMCPServer
from .asset_providers import get_polyhaven_handlers, get_hyper3d_handlers, get_sketchfab_handlers
from .ui_panel import (
    BLENDER_AUTO_MCP_PT_Panel,
    BLENDER_AUTO_MCP_OT_SetFreeTrialHyper3DAPIKey,
    BLENDER_AUTO_MCP_OT_StartServer,
    BLENDER_AUTO_MCP_OT_StopServer,
    BLENDER_AUTO_MCP_OT_BackgroundKeepAlive,
    register_properties,
    unregister_properties
)
from .utils import (
    load_environment_config,
    auto_start_server,
    register_handlers,
    unregister_handlers
)

# Shared global server instance
global_server = None

# Update utils and ui_panel modules to use our global_server
from . import utils, ui_panel
utils.global_server = global_server
ui_panel.global_server = global_server

# Classes to register
classes = [
    BLENDER_AUTO_MCP_PT_Panel,
    BLENDER_AUTO_MCP_OT_SetFreeTrialHyper3DAPIKey,
    BLENDER_AUTO_MCP_OT_StartServer,
    BLENDER_AUTO_MCP_OT_StopServer,
    BLENDER_AUTO_MCP_OT_BackgroundKeepAlive,
]


def register():
    """Register all classes and start auto-server if configured"""
    print("Registering Blender Auto MCP addon...")
    
    # Register all classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    register_properties()
    
    # Register event handlers
    register_handlers()
    
    # Auto-start server if configured via environment variables
    auto_start_server()
    
    print("Blender Auto MCP addon registered successfully")


def unregister():
    """Unregister all classes and stop server"""
    print("Unregistering Blender Auto MCP addon...")
    
    # Stop server if running
    global global_server
    if global_server:
        global_server.stop()
        global_server = None
    
    # Update submodules
    utils.global_server = None
    ui_panel.global_server = None
    
    # Unregister handlers
    unregister_handlers()
    
    # Unregister properties
    unregister_properties()
    
    # Unregister all classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("Blender Auto MCP addon unregistered successfully")


if __name__ == "__main__":
    register()