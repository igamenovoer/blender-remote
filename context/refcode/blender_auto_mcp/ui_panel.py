import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty

from .utils import load_environment_config


# Global server instance
global_server = None

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"


class BLENDER_AUTO_MCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender Auto MCP"
    bl_idname = "BLENDER_AUTO_MCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Auto MCP'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Main server configuration section
        main_box = layout.box()
        main_col = main_box.column()
        
        # Environment variable status
        config = load_environment_config()
        main_col.label(text="Environment Configuration:", icon='PREFERENCES')
        row = main_col.row()
        row.label(text=f"Port: {config['port']}")
        row.label(text=f"Auto-start: {'Yes' if config['start_now'] else 'No'}")
        
        main_col.separator()
        
        main_col.prop(scene, "blender_auto_mcp_port")
        main_col.prop(scene, "blender_auto_mcp_use_polyhaven", text="Use assets from Poly Haven")

        main_col.prop(scene, "blender_auto_mcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blender_auto_mcp_use_hyper3d:
            main_col.prop(scene, "blender_auto_mcp_hyper3d_mode", text="Rodin Mode")
            main_col.prop(scene, "blender_auto_mcp_hyper3d_api_key", text="API Key")
            main_col.operator("blender_auto_mcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")
        
        main_col.prop(scene, "blender_auto_mcp_use_sketchfab", text="Use assets from Sketchfab")
        if scene.blender_auto_mcp_use_sketchfab:
            main_col.prop(scene, "blender_auto_mcp_sketchfab_api_key", text="API Key")
        
        main_col.separator()
        
        if not scene.blender_auto_mcp_server_running:
            main_col.operator("blender_auto_mcp.start_server", text="Start MCP Server")
        else:
            main_col.operator("blender_auto_mcp.stop_server", text="Stop MCP Server")
            main_col.label(text=f"Running on port {scene.blender_auto_mcp_port}")
        
        layout.separator()
        
        # Usage Guide section
        guide_box = layout.box()
        guide_col = guide_box.column()
        
        # Main usage guide header
        guide_header = guide_col.row()
        guide_header.prop(scene, "blender_auto_mcp_show_usage_guide", 
                         icon="TRIA_DOWN" if scene.blender_auto_mcp_show_usage_guide else "TRIA_RIGHT", 
                         text="Usage Guide", emboss=False)
        
        if scene.blender_auto_mcp_show_usage_guide:
            guide_col.separator()
            
            # Environment Variables section
            env_box = guide_col.box()
            env_header = env_box.row()
            env_header.prop(scene, "blender_auto_mcp_show_env_vars", 
                           icon="TRIA_DOWN" if scene.blender_auto_mcp_show_env_vars else "TRIA_RIGHT", 
                           text="Environment Variables", emboss=False)
            
            if scene.blender_auto_mcp_show_env_vars:
                env_col = env_box.column()
                env_col.label(text="Configure these before starting Blender:", icon='INFO')
                env_col.separator(factor=0.5)
                
                # Port configuration
                port_row = env_col.row()
                port_row.label(text="BLENDER_AUTO_MCP_SERVICE_PORT")
                env_col.label(text="  Set custom port (default: 9876)")
                env_col.label(text="  Example: export BLENDER_AUTO_MCP_SERVICE_PORT=9876")
                env_col.separator(factor=0.3)
                
                # Auto-start configuration
                start_row = env_col.row()
                start_row.label(text="BLENDER_AUTO_MCP_START_NOW")
                env_col.label(text="  Auto-start server on addon load")
                env_col.label(text="  Example: export BLENDER_AUTO_MCP_START_NOW=1")
            
            # Background Mode section
            bg_box = guide_col.box()
            bg_header = bg_box.row()
            bg_header.prop(scene, "blender_auto_mcp_show_background_mode", 
                          icon="TRIA_DOWN" if scene.blender_auto_mcp_show_background_mode else "TRIA_RIGHT", 
                          text="Background Mode", emboss=False)
            
            if scene.blender_auto_mcp_show_background_mode:
                bg_col = bg_box.column()
                bg_col.label(text="Run Blender headlessly with MCP server:", icon='CONSOLE')
                bg_col.separator(factor=0.5)
                
                bg_col.label(text="Basic headless mode:")
                bg_col.label(text="  blender --background --python-expr \"import bpy; bpy.ops.preferences.addon_enable(module='blender_auto_mcp')\"")
                bg_col.separator(factor=0.3)
                
                bg_col.label(text="With environment variables:")
                bg_col.label(text="  export BLENDER_AUTO_MCP_START_NOW=1")
                bg_col.label(text="  export BLENDER_AUTO_MCP_SERVICE_PORT=9876")
                bg_col.label(text="  blender --background")
                bg_col.separator(factor=0.3)
                
                bg_col.label(text="Server will auto-start and keep Blender alive")
                bg_col.label(text="Use SIGTERM or SIGINT to gracefully shutdown")
            
            # API Setup section
            api_box = guide_col.box()
            api_header = api_box.row()
            api_header.prop(scene, "blender_auto_mcp_show_api_setup", 
                           icon="TRIA_DOWN" if scene.blender_auto_mcp_show_api_setup else "TRIA_RIGHT", 
                           text="API Setup", emboss=False)
            
            if scene.blender_auto_mcp_show_api_setup:
                api_col = api_box.column()
                api_col.label(text="Configure external service APIs:", icon='WORLD')
                api_col.separator(factor=0.5)
                
                # PolyHaven setup
                api_col.label(text="PolyHaven (Free):")
                api_col.label(text="  • Check 'Use assets from Poly Haven'")
                api_col.label(text="  • No API key required")
                api_col.label(text="  • Access to HDRIs, textures, and models")
                api_col.separator(factor=0.3)
                
                # Hyper3D setup
                api_col.label(text="Hyper3D Rodin (Paid/Trial):")
                api_col.label(text="  • Get API key from hyper3d.ai or fal.ai")
                api_col.label(text="  • Check 'Use Hyper3D Rodin 3D model generation'")
                api_col.label(text="  • Select platform and enter API key")
                api_col.label(text="  • Or use 'Set Free Trial API Key' button")
                api_col.separator(factor=0.3)
                
                # Sketchfab setup
                api_col.label(text="Sketchfab (Account Required):")
                api_col.label(text="  • Create account at sketchfab.com")
                api_col.label(text="  • Get API token from account settings")
                api_col.label(text="  • Check 'Use assets from Sketchfab'")
                api_col.label(text="  • Enter your API token")
            
            # MCP Commands section
            cmd_box = guide_col.box()
            cmd_header = cmd_box.row()
            cmd_header.prop(scene, "blender_auto_mcp_show_mcp_commands", 
                           icon="TRIA_DOWN" if scene.blender_auto_mcp_show_mcp_commands else "TRIA_RIGHT", 
                           text="Available MCP Commands", emboss=False)
            
            if scene.blender_auto_mcp_show_mcp_commands:
                cmd_col = cmd_box.column()
                cmd_col.label(text="Core commands available via MCP:", icon='TOOL_SETTINGS')
                cmd_col.separator(factor=0.5)
                
                # Core commands
                cmd_col.label(text="Scene & Objects:")
                cmd_col.label(text="  • get_scene_info - Get scene overview")
                cmd_col.label(text="  • get_object_info - Detailed object data")
                cmd_col.label(text="  • get_viewport_screenshot - Capture viewport")
                cmd_col.label(text="  • execute_code - Run Python code")
                cmd_col.separator(factor=0.3)
                
                # PolyHaven commands
                cmd_col.label(text="PolyHaven (when enabled):")
                cmd_col.label(text="  • get_polyhaven_categories - List asset categories")
                cmd_col.label(text="  • search_polyhaven_assets - Search for assets")
                cmd_col.label(text="  • download_polyhaven_asset - Download and import")
                cmd_col.label(text="  • set_texture - Apply texture to object")
                cmd_col.separator(factor=0.3)
                
                # Hyper3D commands
                cmd_col.label(text="Hyper3D Rodin (when enabled):")
                cmd_col.label(text="  • create_rodin_job - Generate 3D model")
                cmd_col.label(text="  • poll_rodin_job_status - Check generation status")
                cmd_col.label(text="  • import_generated_asset - Import result")
                cmd_col.separator(factor=0.3)
                
                # Sketchfab commands
                cmd_col.label(text="Sketchfab (when enabled):")
                cmd_col.label(text="  • search_sketchfab_models - Search models")
                cmd_col.label(text="  • download_sketchfab_model - Download model")
                cmd_col.separator(factor=0.3)
                
                # Status commands
                cmd_col.label(text="Status & Control:")
                cmd_col.label(text="  • get_polyhaven_status - Check PolyHaven status")
                cmd_col.label(text="  • get_hyper3d_status - Check Hyper3D status")
                cmd_col.label(text="  • get_sketchfab_status - Check Sketchfab status")
                cmd_col.label(text="  • server_shutdown - Graceful shutdown")


# Operator to set Hyper3D API Key
class BLENDER_AUTO_MCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blender_auto_mcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"
    
    def execute(self, context):
        context.scene.blender_auto_mcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blender_auto_mcp_hyper3d_mode = 'MAIN_SITE'
        self.report({'INFO'}, "API Key set successfully!")
        return {'FINISHED'}


# Operator to start the server
class BLENDER_AUTO_MCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blender_auto_mcp.start_server"
    bl_label = "Start MCP Server"
    bl_description = "Start the Blender Auto MCP server"
    
    def execute(self, context):
        from .server import BlenderAutoMCPServer
        import blender_auto_mcp
        scene = context.scene
        
        # Stop existing server if it's running on a different port
        if blender_auto_mcp.global_server and blender_auto_mcp.global_server.port != scene.blender_auto_mcp_port:
            print(f"Stopping existing server on port {blender_auto_mcp.global_server.port} to start on new port {scene.blender_auto_mcp_port}")
            blender_auto_mcp.global_server.stop()
            blender_auto_mcp.global_server = None
        
        # Create a new server instance with the GUI port
        if not blender_auto_mcp.global_server:
            blender_auto_mcp.global_server = BlenderAutoMCPServer(port=scene.blender_auto_mcp_port)
        
        # Start the server and check if it succeeded
        success = blender_auto_mcp.global_server.start()
        if success:
            scene.blender_auto_mcp_server_running = True
            self.report({'INFO'}, f"MCP Server started successfully on port {scene.blender_auto_mcp_port}")
        else:
            scene.blender_auto_mcp_server_running = False
            self.report({'ERROR'}, f"Failed to start MCP Server on port {scene.blender_auto_mcp_port}. Check console for details.")
        
        return {'FINISHED'}


# Operator to stop the server
class BLENDER_AUTO_MCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blender_auto_mcp.stop_server"
    bl_label = "Stop MCP Server"
    bl_description = "Stop the Blender Auto MCP server"
    
    def execute(self, context):
        import blender_auto_mcp
        scene = context.scene
        
        # Stop the server if it exists
        if blender_auto_mcp.global_server:
            blender_auto_mcp.global_server.stop()
            blender_auto_mcp.global_server = None
        
        scene.blender_auto_mcp_server_running = False
        
        return {'FINISHED'}


class BLENDER_AUTO_MCP_OT_BackgroundKeepAlive(bpy.types.Operator):
    """Modal operator to keep Blender alive in background mode when MCP server is running"""
    bl_idname = "blender_auto_mcp.background_keep_alive"
    bl_label = "Background Keep Alive"
    bl_description = "Keep Blender alive in background mode while MCP server is running"
    
    _timer = None
    
    def modal(self, context, event):
        import blender_auto_mcp
        
        if event.type == 'TIMER':
            # Check if server is still running
            if not blender_auto_mcp.global_server or not blender_auto_mcp.global_server.running:
                # Server stopped, cancel modal operator and quit Blender in background mode
                print("MCP server stopped, exiting background mode...")
                self.cancel(context)
                if bpy.app.background:
                    bpy.ops.wm.quit_blender()
                return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        import blender_auto_mcp
        
        # Only run in background mode with an active server
        if not bpy.app.background or not blender_auto_mcp.global_server or not blender_auto_mcp.global_server.running:
            print("Background keep-alive operator cancelled: not in background mode or server not running")
            return {'CANCELLED'}
        
        print("Starting background keep-alive modal operator...")
        
        try:
            # Add timer - check every second
            wm = context.window_manager
            # In background mode, there might not be a window
            self._timer = wm.event_timer_add(1.0, window=None)
            wm.modal_handler_add(self)
            
            print("Background keep-alive modal operator timer and handler added successfully")
            # Return RUNNING_MODAL to keep Blender alive
            return {'RUNNING_MODAL'}
        except Exception as e:
            print(f"Failed to set up background keep-alive modal operator: {e}")
            return {'CANCELLED'}
    
    def cancel(self, context):
        print("Cancelling background keep-alive modal operator...")
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self._timer = None
        return {'CANCELLED'}


def register_properties():
    """Register scene properties"""
    # Load configuration from environment
    config = load_environment_config()
    
    bpy.types.Scene.blender_auto_mcp_port = IntProperty(
        name="Port",
        description="Port for the Blender Auto MCP server",
        default=config['port'],
        min=1024,
        max=65535
    )
    
    bpy.types.Scene.blender_auto_mcp_server_running = BoolProperty(
        name="Server Running",
        default=False
    )
    
    bpy.types.Scene.blender_auto_mcp_use_polyhaven = BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_use_hyper3d = BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generation integration",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_hyper3d_mode = EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE"
    )

    bpy.types.Scene.blender_auto_mcp_hyper3d_api_key = StringProperty(
        name="Hyper3D API Key",
        description="API key for Hyper3D Rodin service",
        default="",
        subtype='PASSWORD'
    )

    bpy.types.Scene.blender_auto_mcp_use_sketchfab = BoolProperty(
        name="Use Sketchfab",
        description="Enable Sketchfab asset integration",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_sketchfab_api_key = StringProperty(
        name="Sketchfab API Key",
        description="API key for Sketchfab service",
        default="",
        subtype='PASSWORD'
    )

    # UI state properties for collapsible sections
    bpy.types.Scene.blender_auto_mcp_show_usage_guide = BoolProperty(
        name="Show Usage Guide",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_show_env_vars = BoolProperty(
        name="Show Environment Variables",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_show_background_mode = BoolProperty(
        name="Show Background Mode",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_show_api_setup = BoolProperty(
        name="Show API Setup",
        default=False
    )

    bpy.types.Scene.blender_auto_mcp_show_mcp_commands = BoolProperty(
        name="Show MCP Commands",
        default=False
    )


def unregister_properties():
    """Unregister scene properties"""
    del bpy.types.Scene.blender_auto_mcp_port
    del bpy.types.Scene.blender_auto_mcp_server_running
    del bpy.types.Scene.blender_auto_mcp_use_polyhaven
    del bpy.types.Scene.blender_auto_mcp_use_hyper3d
    del bpy.types.Scene.blender_auto_mcp_hyper3d_mode
    del bpy.types.Scene.blender_auto_mcp_hyper3d_api_key
    del bpy.types.Scene.blender_auto_mcp_use_sketchfab
    del bpy.types.Scene.blender_auto_mcp_sketchfab_api_key
    del bpy.types.Scene.blender_auto_mcp_show_usage_guide
    del bpy.types.Scene.blender_auto_mcp_show_env_vars
    del bpy.types.Scene.blender_auto_mcp_show_background_mode
    del bpy.types.Scene.blender_auto_mcp_show_api_setup
    del bpy.types.Scene.blender_auto_mcp_show_mcp_commands


# Classes to register
classes = [
    BLENDER_AUTO_MCP_PT_Panel,
    BLENDER_AUTO_MCP_OT_SetFreeTrialHyper3DAPIKey,
    BLENDER_AUTO_MCP_OT_StartServer,
    BLENDER_AUTO_MCP_OT_StopServer,
    BLENDER_AUTO_MCP_OT_BackgroundKeepAlive,
]


def register():
    """Register UI classes and properties"""
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()


def unregister():
    """Unregister UI classes and properties"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()