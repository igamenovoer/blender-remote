import bpy
import os
import sys
import time
import asyncio

def main():
    try:
        # --- Addon Installation ---
        addon_module_name = "tcp_echo"
        
        # Ensure we have a clean slate
        if addon_module_name in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_disable(module=addon_module_name)
            print(f"Disabled existing addon '{addon_module_name}'")

        addon_zip_path = os.path.abspath("blender_plugins/tcp_echo.zip")
        if not os.path.exists(addon_zip_path):
            raise FileNotFoundError(f"Addon zip file not found at: {addon_zip_path}")
        
        print(f"Installing addon from: {addon_zip_path}")
        bpy.ops.preferences.addon_install(filepath=addon_zip_path, overwrite=True)
        
        print(f"Enabling addon '{addon_module_name}'")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
        print(f"Successfully enabled addon '{addon_module_name}'")

        # --- Server Startup ---
        print("Starting server from script...")
        from tcp_echo import start_server_from_script, async_loop, cleanup_server

        start_server_from_script()

        # --- Keep Blender Alive ---
        print("Server started. Entering main loop to keep Blender alive.")
        print("Press Ctrl+C to exit.")
        
        # This loop is now the main process, keeping Blender running
        try:
            while True:
                # This is the heart of the background mode operation.
                # It drives the asyncio event loop, allowing the server to run.
                if async_loop.kick_async_loop():
                    # The loop has no more tasks and wants to stop.
                    break
                time.sleep(0.1) # Prevent high CPU usage
        except SystemExit as e:
            print(f"Caught SystemExit: {e}. Shutting down.")

    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt. Shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("Cleaning up server before exit.")
        # Ensure cleanup is called when the script exits
        if 'cleanup_server' in locals():
            cleanup_server()
        
        # It's good practice to unregister the addon as well
        if 'addon_module_name' in locals() and addon_module_name in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_disable(module=addon_module_name)
            print(f"Disabled addon '{addon_module_name}' on exit.")

    print("Script finished.")

if __name__ == "__main__":
    main()
