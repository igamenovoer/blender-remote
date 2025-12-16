# How to Persist Data in Blender's Memory During a Session

This guide explains how to store data in memory so that it persists and can be shared across different Python scripts, addons, and plugins within a single Blender session. This is particularly useful for sharing state, caching data, or managing session-wide settings without saving them to the `.blend` file. These methods work in both GUI and background (`blender --background`) modes.

There are two primary methods to achieve this:

1.  **Using a Global Variable in a Python Module (Singleton Pattern)**: A standard Python approach that is simple and effective for purely in-memory data.
2.  **Using Custom Properties on a Persistent Blender Data Block**: The "Blender-native" way, which integrates with Blender's data system.

## Method 1: Global Variable in a Python Module (Recommended for Simplicity)

This is the most straightforward method. You create a Python module (a single `.py` file) that holds your shared data. Any other script or addon can then import this module to access or modify the data. As long as Blender is running, the module remains in memory.

### How It Works

When a module is imported in Python, it is loaded into `sys.modules`. Subsequent imports of the same module will reuse the existing module object from the cache. This means any global variables defined in that module will persist throughout the Blender session.

### Example

1.  **Create a shared data module.**
    Create a file named `shared_data.py` and place it in a location where Blender's Python interpreter can find it (e.g., in your addon's folder or in `scripts/modules`).

    ```python
    # shared_data.py

    # This dictionary will hold our session data.
    # It persists as long as this module is in memory.
    session_storage = {
        'user_name': None,
        'is_processing': False,
        'cached_results': {}
    }

    def get_data(key, default=None):
        """Safely retrieve a value from the session storage."""
        return session_storage.get(key, default)

    def set_data(key, value):
        """Set a value in the session storage."""
        session_storage[key] = value
        print(f"[Shared Data] Set '{key}' to '{value}'")

    def clear_data():
        """Clear all session storage."""
        session_storage.clear()
        print("[Shared Data] Storage cleared.")
    ```

2.  **Access the data from another script or addon.**

    ```python
    # script_A.py
    import bpy
    from . import shared_data # Assuming it's in the same addon

    class SetDataOperator(bpy.types.Operator):
        bl_idname = "session.set_data"
        bl_label = "Set Session Data"

        def execute(self, context):
            shared_data.set_data('user_name', 'Alice')
            shared_data.set_data('is_processing', True)
            return {'FINISHED'}
    ```

    ```python
    # script_B.py
    import bpy
    from . import shared_data

    class GetDataOperator(bpy.types.Operator):
        bl_idname = "session.get_data"
        bl_label = "Get Session Data"

        def execute(self, context):
            user = shared_data.get_data('user_name')
            is_proc = shared_data.get_data('is_processing')
            print(f"User: {user}, Processing: {is_proc}")
            # Prints "User: Alice, Processing: True" if script_A ran first.
            return {'FINISHED'}
    ```

### Pros and Cons

-   **Pros**:
    -   Extremely simple and a standard Python pattern.
    -   Can store any Python object (lists, dicts, complex class instances) without serialization.
    -   Completely independent of the `.blend` file and Blender's data blocks.
-   **Cons**:
    -   Data is lost if the addon is reloaded, as this clears and re-imports the modules. This is usually only a concern during development.
    -   It's a "pure Python" solution and doesn't integrate with Blender's property system (e.g., no UI panels generated automatically).

## Method 2: Custom Properties on a Persistent Data Block

This method involves attaching your data to a Blender data block that is guaranteed to exist for the entire session. The best candidate for this is the `bpy.types.WindowManager`.

### How It Works

You can dynamically add custom properties to any ID-type data block in Blender. These properties are essentially key-value pairs stored with the object. By attaching them to a global and persistent object like the `WindowManager`, the data becomes available everywhere.

### Example

1.  **Define your properties using a `PropertyGroup`.**
    This is the cleanest way to manage a structured set of properties.

    ```python
    import bpy

    class MySessionProperties(bpy.types.PropertyGroup):
        """A group of properties to store session data."""
        user_name: bpy.props.StringProperty(name="User Name")
        is_processing: bpy.props.BoolProperty(name="Is Processing", default=False)
        # For complex data like dicts, you can use a StringProperty and JSON.
        cached_results_json: bpy.props.StringProperty(name="Cached Results (JSON)")

    def register():
        bpy.utils.register_class(MySessionProperties)
        # Attach our property group to the WindowManager type.
        # This makes it available on every window manager instance.
        bpy.types.WindowManager.session_data = bpy.props.PointerProperty(type=MySessionProperties)

    def unregister():
        # Clean up when the addon is disabled.
        del bpy.types.WindowManager.session_data
        bpy.utils.unregister_class(MySessionProperties)
    ```

2.  **Access and modify the data.**
    You can now access your session data through `bpy.context.window_manager.session_data`. This works even in background mode, as `bpy.context.window_manager` is available, albeit with limited UI-related functionality.

    ```python
    # script_A.py
    import bpy
    import json

    def set_session_data():
        # Get the session data property group from the window manager.
        session_data = bpy.context.window_manager.session_data

        # Set simple properties directly.
        session_data.user_name = "Bob"
        session_data.is_processing = True

        # For complex data, serialize to JSON.
        my_cache = {"item1": 123, "item2": "data"}
        session_data.cached_results_json = json.dumps(my_cache)

        print(f"Set user to '{session_data.user_name}'")

    # script_B.py
    import bpy
    import json

    def get_session_data():
        session_data = bpy.context.window_manager.session_data

        print(f"User: {session_data.user_name}")
        print(f"Processing: {session_data.is_processing}")

        # Deserialize complex data from JSON.
        if session_data.cached_results_json:
            cached_data = json.loads(session_data.cached_results_json)
            print(f"Cached Item 1: {cached_data.get('item1')}")
    ```

### Pros and Cons

-   **Pros**:
    -   Integrates with Blender's data system.
    -   Data is stored in a structured way using `PropertyGroup`.
    -   Can be easily exposed in UI panels if needed.
-   **Cons**:
    -   More complex to set up than a simple module variable.
    -   Can only store types supported by `bpy.props` (e.g., `StringProperty`, `IntProperty`, `CollectionProperty`). Complex Python objects must be serialized (e.g., to JSON).

## Conclusion: Which Method to Choose?

-   For **simple, purely in-memory data** that doesn't need to be displayed in the UI, the **global variable in a module** (Method 1) is often the quickest and most flexible solution.
-   For **structured data** that might need to be integrated with Blender's UI or other systems, or if you prefer a more "Blender-native" approach, using **custom properties on the `WindowManager`** (Method 2) is the more robust and scalable choice.

Both methods are fully compatible with background mode, making them reliable for any scripting environment in Blender.
