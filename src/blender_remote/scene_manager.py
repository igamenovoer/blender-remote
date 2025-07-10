"""
Blender Scene Manager for accessing and manipulating the 3D scene.
"""

import numpy as np
import trimesh
from typing import Dict, List, Any, Union, Tuple, Optional, cast
from io import BytesIO
import base64

from .client import BlenderMCPClient
from .data_types import (
    SceneObject,
    SceneInfo,
    CameraSettings,
    RenderSettings,
    MaterialSettings,
    ExportSettings,
)
from .exceptions import BlenderMCPError, BlenderCommandError


class BlenderSceneManager:
    """
    Blender Scene Manager for accessing and manipulating the 3D scene.

    Provides high-level methods for scene operations including object creation,
    manipulation, camera control, and rendering.

    Parameters
    ----------
    client : BlenderMCPClient
        BlenderMCPClient instance for communication.

    Attributes
    ----------
    client : BlenderMCPClient
        MCP client for Blender communication.
    """

    def __init__(self, client: BlenderMCPClient):
        """
        Initialize scene manager.

        Parameters
        ----------
        client : BlenderMCPClient
            BlenderMCPClient instance for communication.
        """
        self.client = client

    @classmethod
    def from_client(cls, client: BlenderMCPClient) -> "BlenderSceneManager":
        """
        Create BlenderSceneManager from existing BlenderMCPClient.

        Parameters
        ----------
        client : BlenderMCPClient
            Existing BlenderMCPClient instance.

        Returns
        -------
        BlenderSceneManager
            New BlenderSceneManager instance using the provided client.
        """
        return cls(client)

    def get_scene_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current scene.

        Returns
        -------
        dict
            Dictionary with scene info (objects, materials, etc.).
        """
        return self.client.get_scene_info()

    def get_scene_info(self) -> SceneInfo:
        """
        Get comprehensive scene information as structured data.

        Returns
        -------
        SceneInfo
            SceneInfo object with all scene data.
        """
        summary = self.get_scene_summary()

        # Convert objects to SceneObject instances
        objects = []
        for obj_data in summary.get("objects", []):
            objects.append(
                SceneObject(
                    name=obj_data.get("name", ""),
                    type=obj_data.get("type", ""),
                    location=obj_data.get("location", [0, 0, 0]),
                    rotation=obj_data.get("rotation", [1, 0, 0, 0]),
                    scale=obj_data.get("scale", [1, 1, 1]),
                    visible=obj_data.get("visible", True),
                )
            )

        # Convert materials to MaterialSettings instances
        materials = []
        for mat_data in summary.get("materials", []):
            materials.append(
                MaterialSettings(
                    name=mat_data.get("name", ""),
                    color=mat_data.get("color", [0.8, 0.8, 0.8, 1.0]),
                    metallic=mat_data.get("metallic", 0.0),
                    roughness=mat_data.get("roughness", 0.5),
                    emission=mat_data.get("emission", [0.0, 0.0, 0.0]),
                    emission_strength=mat_data.get("emission_strength", 0.0),
                )
            )

        # Extract camera settings if available
        camera = None
        camera_data = summary.get("camera")
        if camera_data:
            camera = CameraSettings(
                location=camera_data.get("location", [7, -7, 5]),
                target=camera_data.get("target", [0, 0, 0]),
                fov=camera_data.get("fov", 50.0),
                lens=camera_data.get("lens", 50.0),
            )

        # Extract render settings
        render_data = summary.get("render", {})
        render_settings = RenderSettings(
            resolution=render_data.get("resolution", [1920, 1080]),
            samples=render_data.get("samples", 128),
            engine=render_data.get("engine", "CYCLES"),
            output_path=render_data.get("output_path", ""),
        )

        return SceneInfo(
            objects=objects,
            materials=materials,
            camera=camera,
            render_settings=render_settings,
            collections=summary.get("collections", []),
        )

    def list_objects(self, object_type: Optional[str] = None) -> List[SceneObject]:
        """
        List objects in the scene.

        Parameters
        ----------
        object_type : str, optional
            Filter by object type (e.g., "MESH", "CAMERA", "LIGHT").

        Returns
        -------
        list of SceneObject
            List of SceneObject instances with object info.
        """
        type_condition = f'obj.type == "{object_type}"' if object_type else "True"
        code = f"""
import bpy

objects_data = []
for obj in bpy.context.scene.objects:
    if {type_condition}:
        objects_data.append({{
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_quaternion),
            "scale": list(obj.scale),
            "visible": obj.visible_get()
        }})

print("OBJECTS_JSON:" + str(objects_data))
"""
        result = self.client.execute_python(code)

        # Extract JSON from output and create SceneObject instances
        for line in result.split("\n"):
            if line.startswith("OBJECTS_JSON:"):
                import ast

                objects_data = ast.literal_eval(line[13:])

                # Convert to SceneObject instances
                scene_objects = []
                for obj_data in objects_data:
                    scene_objects.append(
                        SceneObject(
                            name=obj_data["name"],
                            type=obj_data["type"],
                            location=obj_data["location"],
                            rotation=obj_data["rotation"],
                            scale=obj_data["scale"],
                            visible=obj_data["visible"],
                        )
                    )

                return scene_objects

        return []

    def get_objects_top_level(self) -> List[SceneObject]:
        """
        Get top-level objects directly under the Scene Collection.

        Returns
        -------
        list of SceneObject
            List of SceneObject instances with top-level object info.
        """
        code = """
import bpy

objects_data = []
scene_collection = bpy.context.scene.collection

# Get objects directly in the scene collection (not in sub-collections)
for obj in scene_collection.objects:
    objects_data.append({
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_quaternion),
        "scale": list(obj.scale),
        "visible": obj.visible_get()
    })

print("TOP_LEVEL_OBJECTS_JSON:" + str(objects_data))
"""
        result = self.client.execute_python(code)

        # Extract JSON from output and create SceneObject instances
        for line in result.split("\n"):
            if line.startswith("TOP_LEVEL_OBJECTS_JSON:"):
                import ast

                objects_data = ast.literal_eval(line[23:])

                # Convert to SceneObject instances
                scene_objects = []
                for obj_data in objects_data:
                    scene_objects.append(
                        SceneObject(
                            name=obj_data["name"],
                            type=obj_data["type"],
                            location=obj_data["location"],
                            rotation=obj_data["rotation"],
                            scale=obj_data["scale"],
                            visible=obj_data["visible"],
                        )
                    )

                return scene_objects

        return []

    def update_scene_objects(self, scene_objects: List[SceneObject]) -> Dict[str, bool]:
        """
        Update objects in the Blender scene with new properties.

        Parameters
        ----------
        scene_objects : list of SceneObject
            List of SceneObject instances with updated properties.
            Note: SceneObject.type is not changeable and will be ignored.

        Returns
        -------
        dict
            Dictionary mapping object names to success status (True/False).
        """
        if not scene_objects:
            return {}

        # Build update commands for all objects
        update_commands = []
        object_names = []

        for obj in scene_objects:
            object_names.append(obj.name)

            # Convert quaternion to list for Blender
            quat_list = obj.rotation.tolist()
            loc_list = obj.location.tolist()
            scale_list = obj.scale.tolist()

            update_commands.append(
                f"""
if "{obj.name}" in bpy.data.objects:
    obj = bpy.data.objects["{obj.name}"]
    obj.location = ({loc_list[0]}, {loc_list[1]}, {loc_list[2]})
    obj.rotation_quaternion = ({quat_list[0]}, {quat_list[1]}, {quat_list[2]}, {quat_list[3]})
    obj.scale = ({scale_list[0]}, {scale_list[1]}, {scale_list[2]})
    obj.hide_viewport = {not obj.visible}
    obj.hide_render = {not obj.visible}
    update_results["{obj.name}"] = True
else:
    update_results["{obj.name}"] = False"""
            )

        # Combine all commands into single Python script
        code = f"""
import bpy

update_results = {{}}

{chr(10).join(update_commands)}

print("UPDATE_RESULTS:" + str(update_results))
"""

        result = self.client.execute_python(code)

        # Extract results from output
        for line in result.split("\n"):
            if line.startswith("UPDATE_RESULTS:"):
                import ast

                return cast(Dict[str, bool], ast.literal_eval(line[15:]))

        # Return default failure results if parsing failed
        return {name: False for name in object_names}

    def clear_scene(self, keep_camera: bool = True, keep_light: bool = True) -> bool:
        """
        Clear all objects from the scene.

        Parameters
        ----------
        keep_camera : bool, default True
            Whether to keep camera objects.
        keep_light : bool, default True
            Whether to keep light objects.

        Returns
        -------
        bool
            True if successful.
        """
        keep_types = []
        if keep_camera:
            keep_types.append("CAMERA")
        if keep_light:
            keep_types.append("LIGHT")

        code = f"""
import bpy

# Select objects to delete
bpy.ops.object.select_all(action='DESELECT')
keep_types = {keep_types}

for obj in bpy.context.scene.objects:
    if obj.type not in keep_types:
        obj.select_set(True)

# Delete selected objects
bpy.ops.object.delete()

print("CLEAR_SUCCESS:True")
"""
        result = self.client.execute_python(code)
        return "CLEAR_SUCCESS:True" in result

    def add_primitive(
        self,
        primitive_type: str,
        location: Union[np.ndarray, Tuple[float, float, float], None] = None,
        rotation: Union[np.ndarray, Tuple[float, float, float], None] = None,
        scale: Union[np.ndarray, Tuple[float, float, float], None] = None,
        name: Optional[str] = None,
    ) -> str:
        """
        Add a primitive object to the scene.

        Parameters
        ----------
        primitive_type : str
            Type of primitive ("cube", "sphere", "cylinder", "plane", etc.).
        location : numpy.ndarray or tuple of float, default (0, 0, 0)
            Object location (x, y, z).
        rotation : numpy.ndarray or tuple of float, default (0, 0, 0)
            Object rotation in radians (x, y, z).
        scale : numpy.ndarray or tuple of float, default (1, 1, 1)
            Object scale (x, y, z).
        name : str, optional
            Optional name for the object.

        Returns
        -------
        str
            Name of the created object.
        """
        # Default values
        if location is None:
            location = np.array([0.0, 0.0, 0.0])
        if rotation is None:
            rotation = np.array([0.0, 0.0, 0.0])
        if scale is None:
            scale = np.array([1.0, 1.0, 1.0])

        # Convert to numpy arrays if needed
        location = np.asarray(location, dtype=np.float64)
        rotation = np.asarray(rotation, dtype=np.float64)
        scale = np.asarray(scale, dtype=np.float64)

        # Validate shapes
        if location.shape != (3,):
            raise ValueError("location must be a 3-element array or tuple")
        if rotation.shape != (3,):
            raise ValueError("rotation must be a 3-element array or tuple")
        if scale.shape != (3,):
            raise ValueError("scale must be a 3-element array or tuple")

        loc_str = f"({location[0]}, {location[1]}, {location[2]})"
        rot_str = f"({rotation[0]}, {rotation[1]}, {rotation[2]})"
        scale_str = f"({scale[0]}, {scale[1]}, {scale[2]})"

        name_assignment = f'obj.name = "{name}"' if name else ""
        code = f"""
import bpy

# Add primitive
bpy.ops.mesh.primitive_{primitive_type}_add(location={loc_str})

# Get the created object
obj = bpy.context.active_object

# Set properties
obj.rotation_euler = {rot_str}
obj.scale = {scale_str}

# Set name if provided
{name_assignment}

print("OBJECT_NAME:" + str(obj.name))
"""
        result = self.client.execute_python(code)

        # Extract object name
        for line in result.split("\n"):
            if line.startswith("OBJECT_NAME:"):
                return line[12:]

        return ""

    def add_cube(
        self,
        location: Union[np.ndarray, Tuple[float, float, float], None] = None,
        size: float = 2.0,
        name: Optional[str] = None,
    ) -> str:
        """
        Add a cube to the scene.

        Parameters
        ----------
        location : numpy.ndarray or tuple of float, default (0, 0, 0)
            Cube location (x, y, z).
        size : float, default 2.0
            Cube size (edge length).
        name : str, optional
            Optional name for the cube.

        Returns
        -------
        str
            Name of the created cube.
        """
        if location is None:
            location = np.array([0.0, 0.0, 0.0])
        scale = np.array([size / 2, size / 2, size / 2])
        return self.add_primitive("cube", location=location, scale=scale, name=name)

    def add_sphere(
        self,
        location: Union[np.ndarray, Tuple[float, float, float], None] = None,
        radius: float = 1.0,
        name: Optional[str] = None,
    ) -> str:
        """
        Add a sphere to the scene.

        Parameters
        ----------
        location : numpy.ndarray or tuple of float, default (0, 0, 0)
            Sphere location (x, y, z).
        radius : float, default 1.0
            Sphere radius.
        name : str, optional
            Optional name for the sphere.

        Returns
        -------
        str
            Name of the created sphere.
        """
        if location is None:
            location = np.array([0.0, 0.0, 0.0])
        scale = np.array([radius, radius, radius])
        return self.add_primitive(
            "uv_sphere", location=location, scale=scale, name=name
        )

    def add_cylinder(
        self,
        location: Union[np.ndarray, Tuple[float, float, float], None] = None,
        radius: float = 1.0,
        depth: float = 2.0,
        name: Optional[str] = None,
    ) -> str:
        """
        Add a cylinder to the scene.

        Parameters
        ----------
        location : numpy.ndarray or tuple of float, default (0, 0, 0)
            Cylinder location (x, y, z).
        radius : float, default 1.0
            Cylinder radius.
        depth : float, default 2.0
            Cylinder depth (height).
        name : str, optional
            Optional name for the cylinder.

        Returns
        -------
        str
            Name of the created cylinder.
        """
        if location is None:
            location = np.array([0.0, 0.0, 0.0])
        scale = np.array([radius, radius, depth / 2])
        return self.add_primitive("cylinder", location=location, scale=scale, name=name)

    def delete_object(self, object_name: str) -> bool:
        """
        Delete an object by name.

        Parameters
        ----------
        object_name : str
            Name of object to delete.

        Returns
        -------
        bool
            True if object was deleted.
        """
        code = f"""
import bpy

success = False
if "{object_name}" in bpy.data.objects:
    obj = bpy.data.objects["{object_name}"]
    bpy.data.objects.remove(obj, do_unlink=True)
    success = True

print("DELETE_SUCCESS:" + str(success))
"""
        result = self.client.execute_python(code)
        return "DELETE_SUCCESS:True" in result

    def move_object(
        self, object_name: str, location: Union[np.ndarray, Tuple[float, float, float]]
    ) -> bool:
        """
        Move an object to a new location.

        Parameters
        ----------
        object_name : str
            Name of object to move.
        location : numpy.ndarray or tuple of float
            New location (x, y, z).

        Returns
        -------
        bool
            True if object was moved.
        """
        # Convert to numpy array and validate
        location = np.asarray(location, dtype=np.float64)
        if location.shape != (3,):
            raise ValueError("location must be a 3-element array or tuple")

        code = f"""
import bpy

success = False
if "{object_name}" in bpy.data.objects:
    obj = bpy.data.objects["{object_name}"]
    obj.location = ({location[0]}, {location[1]}, {location[2]})
    success = True

print("MOVE_SUCCESS:" + str(success))
"""
        result = self.client.execute_python(code)
        return "MOVE_SUCCESS:True" in result

    def set_camera_location(
        self,
        location: Union[np.ndarray, Tuple[float, float, float]],
        target: Union[np.ndarray, Tuple[float, float, float], None] = None,
    ) -> bool:
        """
        Set camera location and point it at target.

        Parameters
        ----------
        location : numpy.ndarray or tuple of float
            Camera location (x, y, z).
        target : numpy.ndarray or tuple of float, default (0, 0, 0)
            Point to look at (x, y, z).

        Returns
        -------
        bool
            True if camera was positioned.
        """
        # Default target
        if target is None:
            target = np.array([0.0, 0.0, 0.0])

        # Convert to numpy arrays and validate
        location = np.asarray(location, dtype=np.float64)
        target = np.asarray(target, dtype=np.float64)

        if location.shape != (3,):
            raise ValueError("location must be a 3-element array or tuple")
        if target.shape != (3,):
            raise ValueError("target must be a 3-element array or tuple")

        code = f"""
import bpy
import mathutils

# Find camera
camera = None
for obj in bpy.context.scene.objects:
    if obj.type == "CAMERA":
        camera = obj
        break

success = False
if camera:
    # Set location
    camera.location = ({location[0]}, {location[1]}, {location[2]})
    
    # Point at target
    target_loc = mathutils.Vector(({target[0]}, {target[1]}, {target[2]}))
    camera_loc = mathutils.Vector(camera.location)
    direction = target_loc - camera_loc
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    success = True

print("CAMERA_SUCCESS:" + str(success))
"""
        result = self.client.execute_python(code)
        return "CAMERA_SUCCESS:True" in result

    def render_image(
        self, filepath: str, resolution: Union[np.ndarray, Tuple[int, int], None] = None
    ) -> bool:
        """
        Render the current scene to an image file.

        Parameters
        ----------
        filepath : str
            Output file path.
        resolution : numpy.ndarray or tuple of int, default (1920, 1080)
            Render resolution (width, height).

        Returns
        -------
        bool
            True if render successful.
        """
        # Default resolution
        if resolution is None:
            resolution = np.array([1920, 1080], dtype=np.int32)

        # Convert to numpy array and validate
        resolution = np.asarray(resolution, dtype=np.int32)
        if resolution.shape != (2,):
            raise ValueError("resolution must be a 2-element array or tuple")

        code = f"""
import bpy

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = {resolution[0]}
scene.render.resolution_y = {resolution[1]}
scene.render.filepath = "{filepath}"

# Render
try:
    bpy.ops.render.render(write_still=True)
    success = True
except:
    success = False

print("RENDER_SUCCESS:" + str(success))
"""
        result = self.client.execute_python(code)
        return "RENDER_SUCCESS:True" in result

    def get_object_as_glb_raw(
        self,
        object_name: str,
        with_material: bool = True,
        blender_temp_dir: Optional[str] = None,
        keep_temp_file: bool = False,
    ) -> bytes:
        """
        Export a Blender object or collection as GLB and return raw bytes.

        Parameters
        ----------
        object_name : str
            Name of the object or collection to export.
        with_material : bool, default True
            Whether to export materials with the object(s).
        blender_temp_dir : str, optional
            Temporary directory path on the Blender side.
        keep_temp_file : bool, default False
            Whether to keep the temporary GLB file after transfer.

        Returns
        -------
        bytes
            Raw GLB file data as bytes.

        Raises
        ------
        BlenderCommandError
            If object/collection doesn't exist or export fails.
        """
        code = f"""
import bpy
import os
import tempfile
import base64
import time

# Check if it's an object or collection
is_object = "{object_name}" in bpy.data.objects
is_collection = "{object_name}" in bpy.data.collections

if not is_object and not is_collection:
    print("EXPORT_ERROR:'{object_name}' not found as object or collection")
else:
    # Clear selection first
    bpy.ops.object.select_all(action='DESELECT')
    
    if is_object:
        # Select single object
        obj = bpy.data.objects["{object_name}"]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        print(f"EXPORT_INFO:Exporting object '{{obj.name}}'")
        
    elif is_collection:
        # Select all objects in the collection
        collection = bpy.data.collections["{object_name}"]
        selected_count = 0
        
        # Recursively select objects in collection and subcollections
        def select_objects_in_collection(coll):
            global selected_count
            for obj in coll.objects:
                if obj.type == 'MESH':  # Only select mesh objects for GLB export
                    obj.select_set(True)
                    selected_count += 1
                    if bpy.context.view_layer.objects.active is None:
                        bpy.context.view_layer.objects.active = obj
            
            # Recursively handle child collections
            for child_coll in coll.children:
                select_objects_in_collection(child_coll)
        
        select_objects_in_collection(collection)
        print(f"EXPORT_INFO:Exporting collection '{{collection.name}}' with {{selected_count}} mesh objects")
        
        if selected_count == 0:
            print("EXPORT_ERROR:No mesh objects found in collection")
    
    # Check if we have any objects selected
    if bpy.context.selected_objects:
        # Determine temp directory and create if needed
        blender_temp_dir = r"{blender_temp_dir}"
        if blender_temp_dir == "None" or not blender_temp_dir:
            temp_dir = tempfile.gettempdir()
        else:
            temp_dir = blender_temp_dir
            if not os.path.exists(temp_dir):
                try:
                    os.makedirs(temp_dir, exist_ok=True)
                    print(f"EXPORT_INFO:Created temp directory: {{temp_dir}}")
                except Exception as e:
                    print(f"EXPORT_ERROR:Failed to create temp directory '{{temp_dir}}': {{str(e)}}")
        
        # Generate temporary file path
        temp_filepath = os.path.join(temp_dir, f"temp_{{'{object_name}'.replace(' ', '_')}}_{{int(time.time())}}.glb")
        
        try:
            # Export to GLB
            export_materials_value = 'EXPORT' if {with_material} else 'NONE'
            bpy.ops.export_scene.gltf(
                filepath=temp_filepath,
                use_selection=True,
                export_format='GLB',
                export_materials=export_materials_value,
                export_apply=True,  # Apply transforms to get correct object coordinates
                export_yup=False,  # Keep original coordinate system
                export_texcoords=True,
                export_normals=True
            )
            
            # Check if file was created successfully
            if os.path.exists(temp_filepath):
                # Read file as binary and encode to base64
                with open(temp_filepath, 'rb') as f:
                    glb_bytes = f.read()
                
                glb_base64 = base64.b64encode(glb_bytes).decode('utf-8')
                file_size = len(glb_bytes)
                
                print(f"EXPORT_SUCCESS:{{file_size}}")
                print("GLB_BASE64_START")
                print(glb_base64)
                print("GLB_BASE64_END")
                print(f"TEMP_FILE_PATH:{{temp_filepath}}")
                
                # Handle cleanup based on keep_temp_file parameter
                if not {keep_temp_file}:
                    try:
                        os.remove(temp_filepath)
                        print("CLEANUP_SUCCESS:Temp file removed")
                    except OSError as e:
                        print(f"CLEANUP_WARNING:Could not remove temp file: {{str(e)}}")
                else:
                    print(f"TEMP_FILE_KEPT:{{temp_filepath}}")
                    
            else:
                print("EXPORT_ERROR:GLB file was not created")
                
        except Exception as e:
            print(f"EXPORT_ERROR:{{str(e)}}")
    else:
        print("EXPORT_ERROR:No objects selected for export")
"""

        # Execute export in Blender
        result = self.client.execute_python(code)

        # Parse the result to extract base64 data
        export_success = False
        glb_base64 = ""
        file_size = 0

        lines = result.split("\n")
        in_base64_section = False

        for line in lines:
            if line.startswith("EXPORT_SUCCESS:"):
                export_success = True
                file_size = int(line[15:])
            elif line.startswith("EXPORT_ERROR:"):
                error_msg = line[13:]
                raise BlenderCommandError(f"Export failed: {error_msg}")
            elif line == "GLB_BASE64_START":
                in_base64_section = True
            elif line == "GLB_BASE64_END":
                in_base64_section = False
            elif in_base64_section:
                glb_base64 += line

        if not export_success:
            raise BlenderCommandError("Export failed: Unknown error")

        if not glb_base64:
            raise BlenderCommandError("No GLB data received from Blender")

        # Decode base64 to bytes and return raw data
        try:
            glb_bytes = base64.b64decode(glb_base64)

            if len(glb_bytes) != file_size:
                raise BlenderCommandError(
                    f"GLB data size mismatch: expected {file_size}, got {len(glb_bytes)}"
                )

            return glb_bytes

        except Exception as e:
            raise BlenderCommandError(f"Failed to decode GLB data: {str(e)}")

    def get_object_as_glb(
        self,
        object_name: str,
        with_material: bool = True,
        blender_temp_dir: Optional[str] = None,
        keep_temp_file: bool = False,
    ) -> trimesh.Scene:
        """
        Export a Blender object or collection as GLB and load it as a trimesh Scene.

        Parameters
        ----------
        object_name : str
            Name of the object or collection to export.
        with_material : bool, default True
            Whether to export materials with the object(s).
        blender_temp_dir : str, optional
            Temporary directory path on the Blender side.
        keep_temp_file : bool, default False
            Whether to keep the temporary GLB file after transfer.

        Returns
        -------
        trimesh.Scene
            Trimesh Scene object containing the exported geometry and materials.

        Raises
        ------
        BlenderCommandError
            If object/collection doesn't exist or export fails.
        """
        # Get raw GLB data
        glb_bytes = self.get_object_as_glb_raw(
            object_name, with_material, blender_temp_dir, keep_temp_file
        )

        # Load with trimesh from memory using BytesIO
        try:
            glb_file_obj = BytesIO(glb_bytes)
            mesh_data = trimesh.load(glb_file_obj, file_type="glb")

            # Ensure we return a Scene object
            if isinstance(mesh_data, trimesh.Scene):
                return mesh_data
            else:
                # If it's a Geometry, wrap it in a Scene
                scene = trimesh.Scene()
                scene.add_geometry(mesh_data)
                return scene

        except Exception as e:
            raise BlenderCommandError(f"Failed to load GLB with trimesh: {str(e)}")

    def take_screenshot(
        self, filepath: str, max_size: int = 1920, format: str = "png"
    ) -> Dict[str, Any]:
        """
        Capture viewport screenshot.

        Parameters
        ----------
        filepath : str
            Output file path.
        max_size : int, default 1920
            Maximum image dimension in pixels.
        format : str, default "png"
            Image format ("png", "jpg").

        Returns
        -------
        dict
            Dictionary with screenshot info.
        """
        return self.client.take_screenshot(filepath, max_size, format)
