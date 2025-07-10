"""
Blender Asset Manager for accessing and managing asset libraries.
"""

from typing import List, Dict, Any, Optional, cast

from .client import BlenderMCPClient
from .data_types import AssetLibrary, AssetCollection
from .exceptions import BlenderCommandError


class BlenderAssetManager:
    """
    Blender Asset Manager for accessing and managing asset libraries.

    Provides high-level methods for working with Blender asset libraries,
    including listing collections, importing assets, and managing catalogs.

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
        Initialize asset manager.

        Parameters
        ----------
        client : BlenderMCPClient
            BlenderMCPClient instance for communication.
        """
        self.client = client

    @classmethod
    def from_client(cls, client: BlenderMCPClient) -> "BlenderAssetManager":
        """
        Create BlenderAssetManager from existing BlenderMCPClient.

        Parameters
        ----------
        client : BlenderMCPClient
            Existing BlenderMCPClient instance.

        Returns
        -------
        BlenderAssetManager
            New BlenderAssetManager instance using the provided client.
        """
        return cls(client)

    def list_asset_libraries(self) -> List[AssetLibrary]:
        """
        List all configured asset libraries.

        Returns
        -------
        list of AssetLibrary
            List of AssetLibrary objects with library information.
        """
        code = """
import bpy

# Get asset libraries
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries

libraries = []
for lib in asset_libs:
    libraries.append({"name": lib.name, "path": lib.path})

print(f"LIBRARIES_JSON:{libraries}")
"""
        result = self.client.execute_python(code)

        # Extract JSON from output
        for line in result.split("\n"):
            if line.startswith("LIBRARIES_JSON:"):
                import ast

                libraries_data = ast.literal_eval(line[15:])

                # Convert to AssetLibrary objects
                libraries = []
                for lib_data in libraries_data:
                    libraries.append(
                        AssetLibrary(name=lib_data["name"], path=lib_data["path"])
                    )

                return libraries

        return []

    def get_asset_library(self, library_name: str) -> Optional[AssetLibrary]:
        """
        Get a specific asset library by name.

        Parameters
        ----------
        library_name : str
            Name of the asset library.

        Returns
        -------
        AssetLibrary or None
            AssetLibrary object if found, None otherwise.
        """
        libraries = self.list_asset_libraries()
        for lib in libraries:
            if lib.name == library_name:
                return lib
        return None

    def list_library_collections(self, library_name: str) -> List[AssetCollection]:
        """
        List all collections in a specific asset library.

        Parameters
        ----------
        library_name : str
            Name of the asset library.

        Returns
        -------
        list of AssetCollection
            List of AssetCollection objects with collection information.
        """
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

if not target_lib:
    print("COLLECTIONS_JSON:[]")
else:
    collections_data = []
    
    # Walk through .blend files
    for root, dirs, files in os.walk(target_lib.path):
        for file in files:
            if file.lower().endswith(".blend"):
                blend_path = os.path.join(root, file)
                rel_path = os.path.relpath(blend_path, target_lib.path)
                
                try:
                    with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                        if data_from.collections:
                            for collection_name in data_from.collections:
                                collections_data.append({{
                                    "name": collection_name,
                                    "file_path": rel_path,
                                    "objects": []  # Would need to load to get objects
                                }})
                except:
                    pass
    
    print("COLLECTIONS_JSON:" + str(collections_data))
"""
        result = self.client.execute_python(code)

        # Extract JSON from output
        for line in result.split("\n"):
            if line.startswith("COLLECTIONS_JSON:"):
                import ast

                collections_data = ast.literal_eval(line[17:])

                # Convert to AssetCollection objects
                collections = []
                for coll_data in collections_data:
                    collections.append(
                        AssetCollection(
                            name=coll_data["name"],
                            library_name=library_name,
                            file_path=coll_data["file_path"],
                            objects=coll_data.get("objects", []),
                        )
                    )

                return collections

        return []

    def list_library_catalogs(self, library_name: str) -> Dict[str, Any]:
        """
        List all catalogs (directories and .blend files) in a library.

        Parameters
        ----------
        library_name : str
            Name of the asset library.

        Returns
        -------
        dict
            Dictionary with 'directories', 'blend_files', and 'summary' keys.
        """
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

if not target_lib or not os.path.exists(target_lib.path):
    print("CATALOGS_JSON:" + str({{}}))
else:
    try:
        items = os.listdir(target_lib.path)
        directories = []
        blend_files = []
        
        for item in items:
            full_path = os.path.join(target_lib.path, item)
            if os.path.isdir(full_path):
                directories.append(item)
            elif item.lower().endswith(".blend"):
                blend_files.append(item)
        
        catalogs_data = {{
            "directories": sorted(directories),
            "blend_files": sorted(blend_files),
            "summary": {{
                "directory_count": len(directories),
                "blend_count": len(blend_files),
                "total_items": len(directories) + len(blend_files)
            }}
        }}
        
        print("CATALOGS_JSON:" + str(catalogs_data))
    except Exception as e:
        print("CATALOGS_JSON:" + str({{}}))
"""
        result = self.client.execute_python(code)

        # Extract JSON from output
        for line in result.split("\n"):
            if line.startswith("CATALOGS_JSON:"):
                import ast

                return cast(Dict[str, Any], ast.literal_eval(line[14:]))

        return {}

    def import_collection(
        self, library_name: str, file_path: str, collection_name: str
    ) -> bool:
        """
        Import a collection from an asset library.

        Parameters
        ----------
        library_name : str
            Name of the asset library.
        file_path : str
            Relative path to .blend file in library.
        collection_name : str
            Name of collection to import.

        Returns
        -------
        bool
            True if import successful, False otherwise.
        """
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

success = False
if target_lib:
    blend_path = os.path.join(target_lib.path, "{file_path}")
    if os.path.exists(blend_path):
        try:
            # Import collection
            with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                if "{collection_name}" in data_from.collections:
                    data_to.collections = ["{collection_name}"]
            
            # Link to scene
            if "{collection_name}" in bpy.data.collections:
                bpy.context.collection.children.link(bpy.data.collections["{collection_name}"])
                success = True
        except Exception as e:
            pass

print("IMPORT_SUCCESS:" + str(success))
"""
        result = self.client.execute_python(code)
        return "IMPORT_SUCCESS:True" in result

    def search_collections(
        self, library_name: str, search_term: str
    ) -> List[AssetCollection]:
        """
        Search for collections in a library by name.

        Parameters
        ----------
        library_name : str
            Name of the asset library.
        search_term : str
            Search term to match against collection names.

        Returns
        -------
        list of AssetCollection
            List of matching AssetCollection objects.
        """
        all_collections = self.list_library_collections(library_name)
        search_term_lower = search_term.lower()

        return [
            coll for coll in all_collections if search_term_lower in coll.name.lower()
        ]

    def get_collection_info(
        self, library_name: str, file_path: str, collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific collection.

        Parameters
        ----------
        library_name : str
            Name of the asset library.
        file_path : str
            Relative path to .blend file in library.
        collection_name : str
            Name of collection to inspect.

        Returns
        -------
        dict or None
            Dictionary with collection information if found, None otherwise.
        """
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

collection_info = None
if target_lib:
    blend_path = os.path.join(target_lib.path, "{file_path}")
    if os.path.exists(blend_path):
        try:
            with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                if "{collection_name}" in data_from.collections:
                    # Load collection temporarily to get info
                    data_to.collections = ["{collection_name}"]
                    
                    # Get collection info
                    if "{collection_name}" in bpy.data.collections:
                        collection = bpy.data.collections["{collection_name}"]
                        objects = []
                        
                        for obj in collection.objects:
                            objects.append({{
                                "name": obj.name,
                                "type": obj.type
                            }})
                        
                        collection_info = {{
                            "name": collection.name,
                            "objects": objects,
                            "object_count": len(objects),
                            "file_path": "{file_path}"
                        }}
                        
                        # Clean up - remove the temporarily loaded collection
                        bpy.data.collections.remove(collection)
                        
        except Exception as e:
            pass

print("COLLECTION_INFO:" + str(collection_info))
"""
        result = self.client.execute_python(code)

        # Extract information from output
        for line in result.split("\n"):
            if line.startswith("COLLECTION_INFO:"):
                import ast

                info_str = line[16:]
                if info_str != "None":
                    return cast(Dict[str, Any], ast.literal_eval(info_str))

        return None

    def list_blend_files(self, library_name: str, subdirectory: str = "") -> List[str]:
        """
        List all .blend files in a library or subdirectory.

        Parameters
        ----------
        library_name : str
            Name of the asset library.
        subdirectory : str, optional
            Subdirectory within the library to search.

        Returns
        -------
        list of str
            List of relative paths to .blend files.
        """
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

blend_files = []
if target_lib:
    search_path = os.path.join(target_lib.path, "{subdirectory}")
    if os.path.exists(search_path):
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.lower().endswith(".blend"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, target_lib.path)
                        blend_files.append(rel_path)
        except Exception as e:
            pass

print("BLEND_FILES:" + str(blend_files))
"""
        result = self.client.execute_python(code)

        # Extract file list from output
        for line in result.split("\n"):
            if line.startswith("BLEND_FILES:"):
                import ast

                return cast(List[str], ast.literal_eval(line[12:]))

        return []

    def validate_library(self, library_name: str) -> Dict[str, Any]:
        """
        Validate an asset library and return status information.

        Parameters
        ----------
        library_name : str
            Name of the asset library to validate.

        Returns
        -------
        dict
            Dictionary with validation results including 'valid', 'exists', 'accessible', etc.
        """
        library = self.get_asset_library(library_name)
        if not library:
            return {
                "valid": False,
                "exists": False,
                "accessible": False,
                "error": f"Library '{library_name}' not found in configuration",
            }

        # Check if path exists and is accessible
        code = f"""
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "{library_name}":
        target_lib = lib
        break

validation = {{
    "valid": False,
    "exists": False,
    "accessible": False,
    "path": "",
    "blend_count": 0,
    "collection_count": 0
}}

if target_lib:
    validation["path"] = target_lib.path
    validation["exists"] = os.path.exists(target_lib.path)
    
    if validation["exists"]:
        try:
            validation["accessible"] = os.access(target_lib.path, os.R_OK)
            
            if validation["accessible"]:
                # Count blend files and collections
                blend_count = 0
                collection_count = 0
                
                for root, dirs, files in os.walk(target_lib.path):
                    for file in files:
                        if file.lower().endswith(".blend"):
                            blend_count += 1
                            
                            # Try to count collections in this file
                            try:
                                blend_path = os.path.join(root, file)
                                with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                                    if data_from.collections:
                                        collection_count += len(data_from.collections)
                            except:
                                pass
                
                validation["blend_count"] = blend_count
                validation["collection_count"] = collection_count
                validation["valid"] = True
                
        except Exception as e:
            validation["error"] = str(e)

print("VALIDATION:" + str(validation))
"""
        result = self.client.execute_python(code)

        # Extract validation results
        for line in result.split("\n"):
            if line.startswith("VALIDATION:"):
                import ast

                return cast(Dict[str, Any], ast.literal_eval(line[11:]))

        return {
            "valid": False,
            "exists": False,
            "accessible": False,
            "error": "Failed to validate library",
        }
