# Python Client API Reference

This document provides a detailed reference for the Python client API, which allows you to control a Blender instance remotely. The API is divided into three main components:

-   **`BlenderMCPClient`**: A low-level client for direct communication with the `BLD_Remote_MCP` service in Blender.
-   **`BlenderSceneManager`**: A high-level interface for manipulating objects and the 3D scene.
-   **`BlenderAssetManager`**: A high-level interface for managing asset libraries.

---

## `BlenderMCPClient`

This class handles the direct TCP socket communication with the Blender addon. It's responsible for sending commands and receiving raw JSON responses.

**File:** `src/blender_remote/client.py`

### `__init__(self, host, port, timeout)`

Initializes the client.

-   **`host` (str, optional):** The hostname or IP address of the machine running Blender. Defaults to `localhost`.
-   **`port` (int, optional):** The port the `BLD_Remote_MCP` service is running on. Defaults to `6688`.
-   **`timeout` (float, optional):** The socket timeout in seconds. Defaults to `30.0`.

### `from_url(cls, url_string, timeout)`

Creates a client instance from a URL string.

-   **`url_string` (str):** URL in format `blender://host:port` or just `host:port`.
-   **`timeout` (float, optional):** The socket timeout in seconds. Defaults to `30.0`.
-   **Returns (`BlenderMCPClient`):** A new client instance.

### `execute_command(self, command_type, params)`

Executes a raw command on the Blender MCP service.

-   **`command_type` (str):** The command to execute (e.g., `"get_scene_info"`).
-   **`params` (dict, optional):** A dictionary of parameters for the command.
-   **Returns (dict):** The JSON response from the server.

### `execute_python(self, code, send_as_base64, return_as_base64)`

Executes a string of Python code within Blender's context. This is the most versatile method for custom operations.

-   **`code` (str):** The Python code to execute.
-   **`send_as_base64` (bool):** If `True`, the code is base64 encoded for safe transmission. Defaults to `True`.
-   **`return_as_base64` (bool):** If `True`, the result from Blender is expected to be base64 encoded. Defaults to `True`.
-   **Returns (str):** The standard output from the executed code.

**Example:**
```python
# From tests/client-api/test_client_commands.py
code = """
import bpy
print("Hello from Blender!")
print(f"Blender version: {bpy.app.version}")
"""
result = client.execute_python(code)
print(result)
# Expected output:
# Hello from Blender!
# Blender version: (4, 2, 0)
```

### `get_scene_info(self)`

Retrieves a dictionary containing information about the current scene.

-   **Returns (dict):** A summary of scene contents, including objects, materials, etc.

### `get_object_info(self, object_name)`

Gets detailed information for a specific object.

-   **`object_name` (str):** The name of the object to query.
-   **Returns (dict):** A dictionary of the object's properties.

**Example:**
```python
# From tests/client-api/test_client_scene_info.py
try:
    obj_info = client.get_object_info("Cube")
    print(f"Info for 'Cube': {obj_info}")
except Exception as e:
    print(f"Could not get info for 'Cube': {e}")
```

### `take_screenshot(self, filepath, max_size, format)`

Captures the active viewport in Blender. Note that this only works if Blender is running in GUI mode.

-   **`filepath` (str):** The path where the image will be saved *on the machine running Blender*.
-   **`max_size` (int):** The maximum dimension of the output image. Defaults to `1920`.
-   **`format` (str):** The image format (`"png"` or `"jpg"`). Defaults to `"png"`.
-   **Returns (dict):** Information about the saved screenshot.

### `test_connection(self)`

Checks if a connection to the Blender service can be established by sending a simple command.

-   **Returns (bool):** `True` if successful, `False` otherwise.

### `get_status(self)`

Get status information from the BLD Remote MCP service.

-   **Returns (dict):** A dictionary with service status information.

### `send_exit_request(self)`

Sends an exit request to shutdown the BLD Remote MCP service.

-   **Returns (bool):** `True` if the request was sent successfully, `False` otherwise.

### `get_blender_pid(self)`

Gets the process ID of the running Blender instance.

-   **Returns (int):** The process ID, or -1 if it couldn't be determined.

### `kill_blender_process(self)`

Attempts to forcefully terminate the Blender process.

-   **Returns (bool):** `True` if the process was terminated, `False` otherwise.

**Example:**
```python
# Gracefully shutdown
if client.send_exit_request():
    print("Exit request sent")
else:
    # Force kill if graceful shutdown fails
    pid = client.get_blender_pid()
    if pid > 0:
        success = client.kill_blender_process()
        print(f"Process kill: {'successful' if success else 'failed'}")
```

---

## `BlenderSceneManager`

This class provides a more user-friendly, object-oriented API for common scene operations.

**File:** `src/blender_remote/scene_manager.py`

### `__init__(self, client)`

Initializes the scene manager.

-   **`client` (`BlenderMCPClient`):** An instance of the low-level client.

### `from_client(cls, client)`

Creates a scene manager instance from an existing client.

-   **`client` (`BlenderMCPClient`):** An instance of the low-level client.
-   **Returns (`BlenderSceneManager`):** A new scene manager instance.

### `get_scene_summary(self)`

Retrieves a raw dictionary summary of the scene.

-   **Returns (dict):** Same as `client.get_scene_info()`.

### `get_scene_info(self)`

Retrieves a structured `SceneInfo` object containing detailed information about objects, materials, and settings.

-   **Returns (`SceneInfo`):** A dataclass instance with structured scene data.

### `list_objects(self, object_type)`

Lists all objects in the scene, with an optional filter for type.

-   **`object_type` (str, optional):** Filter by type (e.g., `"MESH"`, `"CAMERA"`).
-   **Returns (list[`SceneObject`]):** A list of objects matching the criteria.

### `get_objects_top_level(self)`

Get top-level objects directly under the Scene Collection.

-   **Returns (list of `SceneObject`):** List of `SceneObject` instances with top-level object info.

### `update_scene_objects(self, scene_objects)`

Update objects in the Blender scene with new properties.

-   **`scene_objects` (list of `SceneObject`):** List of `SceneObject` instances with updated properties.
-   **Returns (dict):** Dictionary mapping object names to success status (True/False).

### `clear_scene(self, keep_camera, keep_light)`

Deletes all objects from the scene, with options to preserve cameras and lights.

-   **`keep_camera` (bool):** If `True`, cameras will not be deleted. Defaults to `True`.
-   **`keep_light` (bool):** If `True`, lights will not be deleted. Defaults to `True`.
-   **Returns (bool):** `True` on success.

**Example:**
```python
# From tests/client-api/test_integration_mcp.py
scene_manager.clear_scene(keep_camera=True, keep_light=True)
```

### `delete_object(self, object_name)`

Deletes a single object by its name.

-   **`object_name` (str):** The name of the object to delete.
-   **Returns (bool):** `True` if the object was found and deleted.

**Example:**
```python
# From tests/client-api/test_scene_manager_objects.py
delete_success = scene_manager.delete_object(test_obj_name)
print(f"Delete operation: {'SUCCESS' if delete_success else 'FAILED'}")
```

### `move_object(self, object_name, location)`

Moves an object to a new 3D location.

-   **`object_name` (str):** The name of the object to move.
-   **`location` (tuple or np.ndarray):** The new `(x, y, z)` coordinates.
-   **Returns (bool):** `True` on success.

**Example:**
```python
# From tests/client-api/test_scene_manager_objects.py
success = scene_manager.move_object(test_obj_name, location=(3, 3, 1))
print(f"Move operation: {'SUCCESS' if success else 'FAILED'}")
```

### `set_camera_location(self, location, target)`

Set camera location and point it at a target.

-   **`location` (numpy.ndarray or tuple of float):** Camera location (x, y, z).
-   **`target` (numpy.ndarray or tuple of float, optional):** Point to look at (x, y, z). Defaults to `(0, 0, 0)`.
-   **Returns (bool):** True if camera was positioned.

**Example:**
```python
# From tests/client-api/test_integration_mcp.py
scene_manager.set_camera_location(location=(10, -10, 5), target=(0, 0, 1))
```

### `render_image(self, filepath, resolution)`

Render the current scene to an image file.

-   **`filepath` (str):** Output file path.
-   **`resolution` (numpy.ndarray or tuple of int, optional):** Render resolution (width, height). Defaults to `(1920, 1080)`.
-   **Returns (bool):** True if render successful.

### `get_object_as_glb_raw(self, object_name, ...)`

Exports a Blender object or collection as GLB and return raw bytes.

-   **`object_name` (str):** Name of the object or collection to export.
-   **`with_material` (bool):** Whether to export materials. Defaults to `True`.
-   **Returns (bytes):** Raw GLB file data as bytes.

### `get_object_as_glb(self, object_name, ...)`

Exports a Blender object or collection as GLB and load it as a `trimesh.Scene`.

-   **`object_name` (str):** Name of the object or collection to export.
-   **`with_material` (bool):** Whether to export materials. Defaults to `True`.
-   **Returns (`trimesh.Scene`):** A `trimesh` scene object.

### `take_screenshot(self, filepath, max_size, format)`

Captures the active viewport in Blender. Note that this only works if Blender is running in GUI mode.

-   **`filepath` (str):** The path where the image will be saved *on the machine running Blender*.
-   **`max_size` (int, optional):** The maximum dimension of the output image. Defaults to `1920`.
-   **`format` (str, optional):** The image format (`"png"` or `"jpg"`). Defaults to `"png"`.
-   **Returns (dict):** Information about the saved screenshot.

---

## `BlenderAssetManager`

This class is used to interact with Blender's asset libraries.

**File:** `src/blender_remote/asset_manager.py`

### `__init__(self, client)`

Initializes the asset manager.

-   **`client` (`BlenderMCPClient`):** An instance of the low-level client.

### `from_client(cls, client)`

Creates an asset manager instance from an existing client.

-   **`client` (`BlenderMCPClient`):** An instance of the low-level client.
-   **Returns (`BlenderAssetManager`):** A new asset manager instance.

### `list_asset_libraries(self)`

Lists all the asset libraries configured in Blender's preferences.

-   **Returns (list[`AssetLibrary`]):** A list of configured asset libraries.

**Example:**
```python
# From tests/client-api/test_scene_manager_export.py
libraries = asset_manager.list_asset_libraries()
print(f"Found {len(libraries)} asset libraries:")
for lib in libraries:
    print(f"  - {lib.name}: {lib.path}")
```

### `get_asset_library(self, library_name)`

Get a specific asset library by name.

-   **`library_name` (str):** Name of the asset library.
-   **Returns (`AssetLibrary` or `None`):** The library object if found.

### `list_library_collections(self, library_name)`

Lists all collections found within the `.blend` files of a given library.

-   **`library_name` (str):** The name of the asset library.
-   **Returns (list[`AssetCollection`]):** A list of collections available in the library.

### `list_library_catalogs(self, library_name)`

List all catalogs (directories and .blend files) in a library.

-   **`library_name` (str):** Name of the asset library.
-   **Returns (dict):** Dictionary with 'directories', 'blend_files', and 'summary' keys.

**Example:**
```python
# From tests/client-api/test_scene_manager_export.py
catalogs = asset_manager.list_library_catalogs(test_lib.name)
print(f"Catalog structure: {catalogs}")
if catalogs:
    print(f"  Directories: {len(catalogs.get('directories', []))}")
    print(f"  Blend files: {len(catalogs.get('blend_files', []))}")
```

### `import_collection(self, library_name, file_path, collection_name)`

Imports a collection from a library into the current scene.

-   **`library_name` (str):** The name of the asset library.
-   **`file_path` (str):** The relative path to the `.blend` file within the library.
-   **`collection_name` (str):** The name of the collection to import.
-   **Returns (bool):** `True` on success.

### `search_collections(self, library_name, search_term)`

Searches for collections in a library whose names contain the search term.

-   **`library_name` (str):** The name of the asset library.
-   **`search_term` (str):** The string to search for.
-   **Returns (list[`AssetCollection`]):** A list of matching collections.

**Example:**
```python
# From tests/client-api/test_scene_manager_export.py
results = asset_manager.search_collections(test_lib.name, "chair")
print(f"Search 'chair': {len(results)} results")
for result in results[:2]:  # Show first 2
    print(f"  - {result.name} ({result.file_path})")
```

### `get_collection_info(self, library_name, file_path, collection_name)`

Get detailed information about a specific collection.

-   **`library_name` (str):** Name of the asset library.
-   **`file_path` (str):** Relative path to .blend file in library.
-   **`collection_name` (str):** Name of collection to inspect.
-   **Returns (dict or None):** Dictionary with collection information if found.

### `list_blend_files(self, library_name, subdirectory)`

List all .blend files in a library or subdirectory.

-   **`library_name` (str):** Name of the asset library.
-   **`subdirectory` (str, optional):** Subdirectory within the library to search.
-   **Returns (list of str):** List of relative paths to .blend files.

### `validate_library(self, library_name)`

Validate an asset library and return status information.

-   **`library_name` (str):** Name of the asset library to validate.
-   **Returns (dict):** Dictionary with validation results.
```

**Example:**
```python
# From tests/client-api/test_scene_manager_export.py
asset_manager = blender_remote.create_asset_manager(port=6688)
libraries = asset_manager.list_asset_libraries()
if libraries:
    print(f"Found {len(libraries)} asset libraries.")
    # Validate the first library
    validation = asset_manager.validate_library(libraries[0].name)
    print(f"Validation for '{libraries[0].name}': {validation}")
```
