"""
Blender Asset Manager for accessing and managing asset libraries.
"""

from typing import List, Dict, Any
from .blender_mcp_client import BlenderMCPClient


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
    def from_client(cls, client: BlenderMCPClient) -> 'BlenderAssetManager':
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
    
    def list_asset_libraries(self) -> List[Dict[str, str]]:
        """
        List all configured asset libraries.
        
        Returns
        -------
        list of dict
            List of dictionaries with 'name' and 'path' keys.
        """
        code = '''
import bpy

# Get asset libraries
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries

libraries = []
for lib in asset_libs:
    libraries.append({"name": lib.name, "path": lib.path})

print(f"LIBRARIES_JSON:{libraries}")
'''
        result = self.client.execute_python(code)
        
        # Extract JSON from output
        for line in result.split('\n'):
            if line.startswith("LIBRARIES_JSON:"):
                import ast
                return ast.literal_eval(line[15:])
        
        return []
    
    def list_library_collections(self, library_name: str) -> List[Dict[str, Any]]:
        """
        List all collections in a specific asset library.
        
        Parameters
        ----------
        library_name : str
            Name of the asset library.
            
        Returns
        -------
        list of dict
            List of dictionaries with collection info (file, collections).
        """
        code = '''
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "''' + library_name + '''":
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
                            collections_data.append({
                                "file": rel_path,
                                "collections": list(data_from.collections)
                            })
                except:
                    pass
    
    print("COLLECTIONS_JSON:" + str(collections_data))
'''
        result = self.client.execute_python(code)
        
        # Extract JSON from output
        for line in result.split('\n'):
            if line.startswith("COLLECTIONS_JSON:"):
                import ast
                return ast.literal_eval(line[17:])
        
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
        code = '''
import bpy
import os

# Find library
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries
target_lib = None

for lib in asset_libs:
    if lib.name == "''' + library_name + '''":
        target_lib = lib
        break

if not target_lib or not os.path.exists(target_lib.path):
    print("CATALOGS_JSON:" + str({}))
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
        
        catalogs_data = {
            "directories": sorted(directories),
            "blend_files": sorted(blend_files),
            "summary": {
                "directory_count": len(directories),
                "blend_count": len(blend_files),
                "total_items": len(directories) + len(blend_files)
            }
        }
        
        print("CATALOGS_JSON:" + str(catalogs_data))
    except Exception as e:
        print("CATALOGS_JSON:" + str({}))
'''
        result = self.client.execute_python(code)
        
        # Extract JSON from output
        for line in result.split('\n'):
            if line.startswith("CATALOGS_JSON:"):
                import ast
                return ast.literal_eval(line[14:])
        
        return {}
    
    def import_collection(self, library_name: str, file_path: str, collection_name: str) -> bool:
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
        code = f'''
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
'''
        result = self.client.execute_python(code)
        return "IMPORT_SUCCESS:True" in result