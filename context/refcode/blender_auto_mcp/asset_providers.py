"""
Asset provider functionality extracted from BlenderAutoMCPServer.

This module contains all the asset provider integrations:
- PolyHaven (HDRI, textures, models)
- Hyper3D/Rodin (3D model generation)
- Sketchfab (3D model marketplace)
"""

import bpy
import mathutils
import json
import requests
import tempfile
import traceback
import os
import shutil
import zipfile
from contextlib import suppress

# Rodin free trial key
RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"


# Helper methods
def _get_aabb(obj):
    """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
    if obj.type != 'MESH':
        raise TypeError("Object must be a mesh")

    # Get the bounding box corners in local space
    local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

    # Convert to world coordinates
    world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

    # Compute axis-aligned min/max coordinates
    min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
    max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

    return [
        [*min_corner], [*max_corner]
    ]


def _clean_imported_glb(filepath, mesh_name=None):
    # Get the set of existing objects before import
    existing_objects = set(bpy.data.objects)

    # Import the GLB file
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    # Ensure the context is updated
    bpy.context.view_layer.update()
    
    # Get all imported objects
    imported_objects = list(set(bpy.data.objects) - existing_objects)
    # imported_objects = [obj for obj in bpy.context.view_layer.objects if obj.select_get()]
    
    if not imported_objects:
        print("Error: No objects were imported.")
        return

    # Identify the mesh object
    mesh_obj = None
    
    if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
        mesh_obj = imported_objects[0]
        print("Single mesh imported, no cleanup needed.")
    else:
        if len(imported_objects) == 2:
            empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
            if len(empty_objs) != 1:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return
            parent_obj = empty_objs.pop()
            if len(parent_obj.children) == 1:
                potential_mesh = parent_obj.children[0]
                if potential_mesh.type == 'MESH':
                    print("GLB structure confirmed: Empty node with one mesh child.")
                    
                    # Unparent the mesh from the empty node
                    potential_mesh.parent = None
                    
                    # Remove the empty node
                    bpy.data.objects.remove(parent_obj)
                    print("Removed empty node, keeping only the mesh.")
                    
                    mesh_obj = potential_mesh
                else:
                    print("Error: Child is not a mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return
        else:
            print("Error: Expected an empty node with one mesh child or a single mesh object.")
            return
    
    # Rename the mesh if needed
    try:
        if mesh_obj and mesh_obj.name is not None and mesh_name:
            mesh_obj.name = mesh_name
            if mesh_obj.data.name is not None:
                mesh_obj.data.name = mesh_name
            print(f"Mesh renamed to: {mesh_name}")
    except Exception as e:
        print("Having issue with renaming, give up renaming.")

    return mesh_obj


# PolyHaven asset provider methods
def search_polyhaven_assets(server_instance, asset_type=None, categories=None):
    """Search for assets from Polyhaven with optional filtering"""
    try:
        url = "https://api.polyhaven.com/assets"
        params = {}
        
        if asset_type and asset_type != "all":
            if asset_type not in ["hdris", "textures", "models"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
            params["type"] = asset_type
            
        if categories:
            params["categories"] = categories
            
        response = requests.get(url, params=params)
        if response.status_code == 200:
            # Limit the response size to avoid overwhelming Blender
            assets = response.json()
            # Return only the first 20 assets to keep response size manageable
            limited_assets = {}
            for i, (key, value) in enumerate(assets.items()):
                if i >= 20:  # Limit to 20 assets
                    break
                limited_assets[key] = value
            
            return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
        else:
            return {"error": f"API request failed with status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def download_polyhaven_asset(server_instance, asset_id, asset_type, resolution="1k", file_format=None):
    try:
        # First get the files information
        files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
        if files_response.status_code != 200:
            return {"error": f"Failed to get asset files: {files_response.status_code}"}
        
        files_data = files_response.json()
        
        # Handle different asset types
        if asset_type == "hdris":
            # For HDRIs, download the .hdr or .exr file
            if not file_format:
                file_format = "hdr"  # Default format for HDRIs
            
            if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                file_info = files_data["hdri"][resolution][file_format]
                file_url = file_info["url"]
                
                # For HDRIs, we need to save to a temporary file first
                # since Blender can't properly load HDR data directly from memory
                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                    # Download the file
                    response = requests.get(file_url)
                    if response.status_code != 200:
                        return {"error": f"Failed to download HDRI: {response.status_code}"}
                    
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                try:
                    # Create a new world if none exists
                    if not bpy.data.worlds:
                        bpy.data.worlds.new("World")
                    
                    world = bpy.data.worlds[0]
                    world.use_nodes = True
                    node_tree = world.node_tree
                    
                    # Clear existing nodes
                    for node in node_tree.nodes:
                        node_tree.nodes.remove(node)
                    
                    # Create nodes
                    tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)
                    
                    mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    
                    # Load the image from the temporary file
                    env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                    env_tex.location = (-400, 0)
                    env_tex.image = bpy.data.images.load(tmp_path)
                    
                    # Use a color space that exists in all Blender versions
                    if file_format.lower() == 'exr':
                        # Try to use Linear color space for EXR files
                        try:
                            env_tex.image.colorspace_settings.name = 'Linear'
                        except:
                            # Fallback to Non-Color if Linear isn't available
                            env_tex.image.colorspace_settings.name = 'Non-Color'
                    else:  # hdr
                        # For HDR files, try these options in order
                        for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                            try:
                                env_tex.image.colorspace_settings.name = color_space
                                break  # Stop if we successfully set a color space
                            except:
                                continue
                    
                    background = node_tree.nodes.new(type='ShaderNodeBackground')
                    background.location = (-200, 0)
                    
                    output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                    output.location = (0, 0)
                    
                    # Connect nodes
                    node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                    node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                    node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                    node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
                    
                    # Set as active world
                    bpy.context.scene.world = world
                    
                    # Clean up temporary file
                    try:
                        tempfile._cleanup()  # This will clean up all temporary files
                    except:
                        pass
                    
                    return {
                        "success": True, 
                        "message": f"HDRI {asset_id} imported successfully",
                        "image_name": env_tex.image.name
                    }
                except Exception as e:
                    return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
            else:
                return {"error": f"Requested resolution or format not available for this HDRI"}
                
        elif asset_type == "textures":
            if not file_format:
                file_format = "jpg"  # Default format for textures
            
            downloaded_maps = {}
            
            try:
                for map_type in files_data:
                    if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                        if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                            file_info = files_data[map_type][resolution][file_format]
                            file_url = file_info["url"]
                            
                            # Use NamedTemporaryFile like we do for HDRIs
                            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                # Download the file
                                response = requests.get(file_url)
                                if response.status_code == 200:
                                    tmp_file.write(response.content)
                                    tmp_path = tmp_file.name
                                    
                                    # Load image from temporary file
                                    image = bpy.data.images.load(tmp_path)
                                    image.name = f"{asset_id}_{map_type}.{file_format}"
                                    
                                    # Pack the image into .blend file
                                    image.pack()
                                    
                                    # Set color space based on map type
                                    if map_type in ['color', 'diffuse', 'albedo']:
                                        try:
                                            image.colorspace_settings.name = 'sRGB'
                                        except:
                                            pass
                                    else:
                                        try:
                                            image.colorspace_settings.name = 'Non-Color'
                                        except:
                                            pass
                                    
                                    downloaded_maps[map_type] = image
                                    
                                    # Clean up temporary file
                                    try:
                                        os.unlink(tmp_path)
                                    except:
                                        pass

                if not downloaded_maps:
                    return {"error": f"No texture maps found for the requested resolution and format"}
                
                # Create a new material with the downloaded textures
                mat = bpy.data.materials.new(name=asset_id)
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Clear default nodes
                for node in nodes:
                    nodes.remove(node)
                
                # Create output node
                output = nodes.new(type='ShaderNodeOutputMaterial')
                output.location = (300, 0)
                
                # Create principled BSDF node
                principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                principled.location = (0, 0)
                links.new(principled.outputs[0], output.inputs[0])
                
                # Add texture nodes based on available maps
                tex_coord = nodes.new(type='ShaderNodeTexCoord')
                tex_coord.location = (-800, 0)
                
                mapping = nodes.new(type='ShaderNodeMapping')
                mapping.location = (-600, 0)
                mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
                links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
                
                # Position offset for texture nodes
                x_pos = -400
                y_pos = 300
                
                # Connect different texture maps
                for map_type, image in downloaded_maps.items():
                    tex_node = nodes.new(type='ShaderNodeTexImage')
                    tex_node.location = (x_pos, y_pos)
                    tex_node.image = image
                    
                    # Set color space based on map type
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            tex_node.image.colorspace_settings.name = 'sRGB'
                        except:
                            pass  # Use default if sRGB not available
                    else:
                        try:
                            tex_node.image.colorspace_settings.name = 'Non-Color'
                        except:
                            pass  # Use default if Non-Color not available
                    
                    links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                    
                    # Connect to appropriate input on Principled BSDF
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                    elif map_type.lower() in ['roughness', 'rough']:
                        links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                    elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                        links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                    elif map_type.lower() in ['normal', 'nor']:
                        # Add normal map node
                        normal_map = nodes.new(type='ShaderNodeNormalMap')
                        normal_map.location = (x_pos + 200, y_pos)
                        links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                        links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                    elif map_type in ['displacement', 'disp', 'height']:
                        # Add displacement node
                        disp_node = nodes.new(type='ShaderNodeDisplacement')
                        disp_node.location = (x_pos + 200, y_pos - 200)
                        links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                        links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    
                    y_pos -= 250
                
                return {
                    "success": True, 
                    "message": f"Texture {asset_id} imported as material",
                    "material": mat.name,
                    "maps": list(downloaded_maps.keys())
                }
            
            except Exception as e:
                return {"error": f"Failed to process textures: {str(e)}"}
            
        elif asset_type == "models":
            # For models, prefer glTF format if available
            if not file_format:
                file_format = "gltf"  # Default format for models
            
            if file_format in files_data and resolution in files_data[file_format]:
                file_info = files_data[file_format][resolution][file_format]
                file_url = file_info["url"]
                
                # Create a temporary directory to store the model and its dependencies
                temp_dir = tempfile.mkdtemp()
                main_file_path = ""
                
                try:
                    # Download the main model file
                    main_file_name = file_url.split("/")[-1]
                    main_file_path = os.path.join(temp_dir, main_file_name)
                    
                    response = requests.get(file_url)
                    if response.status_code != 200:
                        return {"error": f"Failed to download model: {response.status_code}"}
                    
                    with open(main_file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Check for included files and download them
                    if "include" in file_info and file_info["include"]:
                        for include_path, include_info in file_info["include"].items():
                            # Get the URL for the included file - this is the fix
                            include_url = include_info["url"]
                            
                            # Create the directory structure for the included file
                            include_file_path = os.path.join(temp_dir, include_path)
                            os.makedirs(os.path.dirname(include_file_path), exist_ok=True)
                            
                            # Download the included file
                            include_response = requests.get(include_url)
                            if include_response.status_code == 200:
                                with open(include_file_path, "wb") as f:
                                    f.write(include_response.content)
                            else:
                                print(f"Failed to download included file: {include_path}")
                    
                    # Import the model into Blender
                    if file_format == "gltf" or file_format == "glb":
                        bpy.ops.import_scene.gltf(filepath=main_file_path)
                    elif file_format == "fbx":
                        bpy.ops.import_scene.fbx(filepath=main_file_path)
                    elif file_format == "obj":
                        bpy.ops.import_scene.obj(filepath=main_file_path)
                    elif file_format == "blend":
                        # For blend files, we need to append or link
                        with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                            data_to.objects = data_from.objects
                        
                        # Link the objects to the scene
                        for obj in data_to.objects:
                            if obj is not None:
                                bpy.context.collection.objects.link(obj)
                    else:
                        return {"error": f"Unsupported model format: {file_format}"}
                    
                    # Get the names of imported objects
                    imported_objects = [obj.name for obj in bpy.context.selected_objects]
                    
                    return {
                        "success": True, 
                        "message": f"Model {asset_id} imported successfully",
                        "imported_objects": imported_objects
                    }
                except Exception as e:
                    return {"error": f"Failed to import model: {str(e)}"}
                finally:
                    # Clean up temporary directory
                    with suppress(Exception):
                        shutil.rmtree(temp_dir)
            else:
                return {"error": f"Requested format or resolution not available for this model"}
            
        else:
            return {"error": f"Unsupported asset type: {asset_type}"}
            
    except Exception as e:
        return {"error": f"Failed to download asset: {str(e)}"}


def set_texture(server_instance, object_name, texture_id):
    """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
    try:
        # Get the object
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        
        # Make sure object can accept materials
        if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
            return {"error": f"Object {object_name} cannot accept materials"}
        
        # Find all images related to this texture and ensure they're properly loaded
        texture_images = {}
        for img in bpy.data.images:
            if img.name.startswith(texture_id + "_"):
                # Extract the map type from the image name
                map_type = img.name.split('_')[-1].split('.')[0]
                
                # Force a reload of the image
                img.reload()
                
                # Ensure proper color space
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        img.colorspace_settings.name = 'sRGB'
                    except:
                        pass
                else:
                    try:
                        img.colorspace_settings.name = 'Non-Color'
                    except:
                        pass
                
                # Ensure the image is packed
                if not img.packed_file:
                    img.pack()
                
                texture_images[map_type] = img
                print(f"Loaded texture map: {map_type} - {img.name}")
                
                # Debug info
                print(f"Image size: {img.size[0]}x{img.size[1]}")
                print(f"Color space: {img.colorspace_settings.name}")
                print(f"File format: {img.file_format}")
                print(f"Is packed: {bool(img.packed_file)}")

        if not texture_images:
            return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}
        
        # Create a new material
        new_mat_name = f"{texture_id}_material_{object_name}"
        
        # Remove any existing material with this name to avoid conflicts
        existing_mat = bpy.data.materials.get(new_mat_name)
        if existing_mat:
            bpy.data.materials.remove(existing_mat)
        
        new_mat = bpy.data.materials.new(name=new_mat_name)
        new_mat.use_nodes = True
        
        # Set up the material nodes
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        
        # Clear default nodes
        nodes.clear()
        
        # Create output node
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (600, 0)
        
        # Create principled BSDF node
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)
        links.new(principled.outputs[0], output.inputs[0])
        
        # Add texture nodes based on available maps
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)
        
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-600, 0)
        mapping.vector_type = 'TEXTURE'  # Changed from default 'POINT' to 'TEXTURE'
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        
        # Position offset for texture nodes
        x_pos = -400
        y_pos = 300
        
        # Connect different texture maps
        for map_type, image in texture_images.items():
            tex_node = nodes.new(type='ShaderNodeTexImage')
            tex_node.location = (x_pos, y_pos)
            tex_node.image = image
            
            # Set color space based on map type
            if map_type.lower() in ['color', 'diffuse', 'albedo']:
                try:
                    tex_node.image.colorspace_settings.name = 'sRGB'
                except:
                    pass  # Use default if sRGB not available
            else:
                try:
                    tex_node.image.colorspace_settings.name = 'Non-Color'
                except:
                    pass  # Use default if Non-Color not available
            
            links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
            
            # Connect to appropriate input on Principled BSDF
            if map_type.lower() in ['color', 'diffuse', 'albedo']:
                links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
            elif map_type.lower() in ['roughness', 'rough']:
                links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
            elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
            elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                # Add normal map node
                normal_map = nodes.new(type='ShaderNodeNormalMap')
                normal_map.location = (x_pos + 200, y_pos)
                links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
            elif map_type.lower() in ['displacement', 'disp', 'height']:
                # Add displacement node
                disp_node = nodes.new(type='ShaderNodeDisplacement')
                disp_node.location = (x_pos + 200, y_pos - 200)
                disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
            
            y_pos -= 250
        
        # Second pass: Connect nodes with proper handling for special cases
        texture_nodes = {}
        
        # First find all texture nodes and store them by map type
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                for map_type, image in texture_images.items():
                    if node.image == image:
                        texture_nodes[map_type] = node
                        break
        
        # Now connect everything using the nodes instead of images
        # Handle base color (diffuse)
        for map_name in ['color', 'diffuse', 'albedo']:
            if map_name in texture_nodes:
                links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                print(f"Connected {map_name} to Base Color")
                break
        
        # Handle roughness
        for map_name in ['roughness', 'rough']:
            if map_name in texture_nodes:
                links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                print(f"Connected {map_name} to Roughness")
                break
        
        # Handle metallic
        for map_name in ['metallic', 'metalness', 'metal']:
            if map_name in texture_nodes:
                links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                print(f"Connected {map_name} to Metallic")
                break
        
        # Handle normal maps
        for map_name in ['gl', 'dx', 'nor']:
            if map_name in texture_nodes:
                normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                normal_map_node.location = (100, 100)
                links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                print(f"Connected {map_name} to Normal")
                break
        
        # Handle displacement
        for map_name in ['displacement', 'disp', 'height']:
            if map_name in texture_nodes:
                disp_node = nodes.new(type='ShaderNodeDisplacement')
                disp_node.location = (300, -200)
                disp_node.inputs['Scale'].default_value = 0.1  # Reduce displacement strength
                links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                print(f"Connected {map_name} to Displacement")
                break
        
        # Handle ARM texture (Ambient Occlusion, Roughness, Metallic)
        if 'arm' in texture_nodes:
            separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
            separate_rgb.location = (-200, -100)
            links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
            
            # Connect Roughness (G) if no dedicated roughness map
            if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                print("Connected ARM.G to Roughness")
            
            # Connect Metallic (B) if no dedicated metallic map
            if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                print("Connected ARM.B to Metallic")
            
            # For AO (R channel), multiply with base color if we have one
            base_color_node = None
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    base_color_node = texture_nodes[map_name]
                    break
            
            if base_color_node:
                mix_node = nodes.new(type='ShaderNodeMixRGB')
                mix_node.location = (100, 200)
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs['Fac'].default_value = 0.8  # 80% influence
                
                # Disconnect direct connection to base color
                for link in base_color_node.outputs['Color'].links:
                    if link.to_socket == principled.inputs['Base Color']:
                        links.remove(link)
                
                # Connect through the mix node
                links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                links.new(separate_rgb.outputs['R'], mix_node.inputs[2])
                links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                print("Connected ARM.R to AO mix with Base Color")
        
        # Handle AO (Ambient Occlusion) if separate
        if 'ao' in texture_nodes:
            base_color_node = None
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    base_color_node = texture_nodes[map_name]
                    break
            
            if base_color_node:
                mix_node = nodes.new(type='ShaderNodeMixRGB')
                mix_node.location = (100, 200)
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs['Fac'].default_value = 0.8  # 80% influence
                
                # Disconnect direct connection to base color
                for link in base_color_node.outputs['Color'].links:
                    if link.to_socket == principled.inputs['Base Color']:
                        links.remove(link)
                
                # Connect through the mix node
                links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
                print("Connected AO to mix with Base Color")
        
        # CRITICAL: Make sure to clear all existing materials from the object
        while len(obj.data.materials) > 0:
            obj.data.materials.pop(index=0)
        
        # Assign the new material to the object
        obj.data.materials.append(new_mat)
        
        # CRITICAL: Make the object active and select it
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # CRITICAL: Force Blender to update the material
        bpy.context.view_layer.update()
        
        # Get the list of texture maps
        texture_maps = list(texture_images.keys())
        
        # Get info about texture nodes for debugging
        material_info = {
            "name": new_mat.name,
            "has_nodes": new_mat.use_nodes,
            "node_count": len(new_mat.node_tree.nodes),
            "texture_nodes": []
        }
        
        for node in new_mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                connections = []
                for output in node.outputs:
                    for link in output.links:
                        connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")
                
                material_info["texture_nodes"].append({
                    "name": node.name,
                    "image": node.image.name,
                    "colorspace": node.image.colorspace_settings.name,
                    "connections": connections
                })
        
        return {
            "success": True,
            "message": f"Created new material and applied texture {texture_id} to {object_name}",
            "material": new_mat.name,
            "maps": texture_maps,
            "material_info": material_info
        }
        
    except Exception as e:
        print(f"Error in set_texture: {str(e)}")
        traceback.print_exc()
        return {"error": f"Failed to apply texture: {str(e)}"}


# Hyper3D/Rodin asset provider methods
def create_rodin_job(server_instance, *args, **kwargs):
    scene = bpy.context.scene
    mode = getattr(scene, 'blender_auto_mcp_hyper3d_mode', 'MAIN_SITE')
    if mode == "MAIN_SITE":
        return create_rodin_job_main_site(server_instance, *args, **kwargs)
    elif mode == "FAL_AI":
        return create_rodin_job_fal_ai(server_instance, *args, **kwargs)
    else:
        return {"error": f"Unknown Hyper3D Rodin mode: {mode}"}


def poll_rodin_job_status(server_instance, *args, **kwargs):
    scene = bpy.context.scene
    mode = getattr(scene, 'blender_auto_mcp_hyper3d_mode', 'MAIN_SITE')
    if mode == "MAIN_SITE":
        return poll_rodin_job_status_main_site(server_instance, *args, **kwargs)
    elif mode == "FAL_AI":
        return poll_rodin_job_status_fal_ai(server_instance, *args, **kwargs)
    else:
        return {"error": f"Unknown Hyper3D Rodin mode: {mode}"}


def import_generated_asset(server_instance, *args, **kwargs):
    scene = bpy.context.scene
    mode = getattr(scene, 'blender_auto_mcp_hyper3d_mode', 'MAIN_SITE')
    if mode == "MAIN_SITE":
        return import_generated_asset_main_site(server_instance, *args, **kwargs)
    elif mode == "FAL_AI":
        return import_generated_asset_fal_ai(server_instance, *args, **kwargs)
    else:
        return {"error": f"Unknown Hyper3D Rodin mode: {mode}"}


def create_rodin_job_main_site(
        server_instance,
        text_prompt: str=None,
        images: list=None,
        bbox_condition=None
    ):
    try:
        if images is None:
            images = []
        scene = bpy.context.scene
        api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
        
        """Call Rodin API, get the job uuid and subscription key"""
        files = [
            *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
            ("tier", (None, "Sketch")),
            ("mesh_mode", (None, "Raw")),
        ]
        if text_prompt:
            files.append(("prompt", (None, text_prompt)))
        if bbox_condition:
            files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/rodin",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            files=files
        )
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}


def create_rodin_job_fal_ai(
        server_instance,
        text_prompt: str=None,
        images: list=None,
        bbox_condition=None
    ):
    try:
        scene = bpy.context.scene
        api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
        
        req_data = {
            "tier": "Sketch",
        }
        if images:
            req_data["input_image_urls"] = images
        if text_prompt:
            req_data["prompt"] = text_prompt
        if bbox_condition:
            req_data["bbox_condition"] = bbox_condition
        response = requests.post(
            "https://queue.fal.run/fal-ai/hyper3d/rodin",
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            json=req_data
        )
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}


def poll_rodin_job_status_main_site(server_instance, subscription_key: str):
    """Call the job status API to get the job status"""
    scene = bpy.context.scene
    api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
    
    response = requests.post(
        "https://hyperhuman.deemos.com/api/v2/status",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "subscription_key": subscription_key,
        },
    )
    data = response.json()
    return {
        "status_list": [i["status"] for i in data["jobs"]]
    }


def poll_rodin_job_status_fal_ai(server_instance, request_id: str):
    """Call the job status API to get the job status"""
    scene = bpy.context.scene
    api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
    
    response = requests.get(
        f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
        headers={
            "Authorization": f"KEY {api_key}",
        },
    )
    data = response.json()
    return data


def import_generated_asset_main_site(server_instance, task_uuid: str, name: str):
    """Fetch the generated asset, import into blender"""
    scene = bpy.context.scene
    api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
    
    response = requests.post(
        "https://hyperhuman.deemos.com/api/v2/download",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            'task_uuid': task_uuid
        }
    )
    data_ = response.json()
    temp_file = None
    for i in data_["list"]:
        if i["name"].endswith(".glb"):
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                prefix=task_uuid,
                suffix=".glb",
            )

            try:
                # Download the content
                response = requests.get(i["url"], stream=True)
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Write the content to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                    
                # Close the file
                temp_file.close()
                
            except Exception as e:
                # Clean up the file if there's an error
                temp_file.close()
                os.unlink(temp_file.name)
                return {"succeed": False, "error": str(e)}
            
            break
    else:
        return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

    try:
        obj = _clean_imported_glb(
            filepath=temp_file.name,
            mesh_name=name
        )
        result = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
        }

        if obj.type == "MESH":
            bounding_box = _get_aabb(obj)
            result["world_bounding_box"] = bounding_box
        
        return {
            "succeed": True, **result
        }
    except Exception as e:
        return {"succeed": False, "error": str(e)}


def import_generated_asset_fal_ai(server_instance, request_id: str, name: str):
    """Fetch the generated asset, import into blender"""
    scene = bpy.context.scene
    api_key = getattr(scene, 'blender_auto_mcp_hyper3d_api_key', '')
    
    response = requests.get(
        f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
        headers={
            "Authorization": f"Key {api_key}",
        }
    )
    data_ = response.json()
    temp_file = None
    
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        prefix=request_id,
        suffix=".glb",
    )

    try:
        # Download the content
        response = requests.get(data_["model_mesh"]["url"], stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Write the content to the temporary file
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
            
        # Close the file
        temp_file.close()
        
    except Exception as e:
        # Clean up the file if there's an error
        temp_file.close()
        os.unlink(temp_file.name)
        return {"succeed": False, "error": str(e)}

    try:
        obj = _clean_imported_glb(
            filepath=temp_file.name,
            mesh_name=name
        )
        result = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
        }

        if obj.type == "MESH":
            bounding_box = _get_aabb(obj)
            result["world_bounding_box"] = bounding_box
        
        return {
            "succeed": True, **result
        }
    except Exception as e:
        return {"succeed": False, "error": str(e)}


# Sketchfab asset provider methods
def search_sketchfab_models(server_instance, query, categories=None, count=20, downloadable=True):
    """Search for models on Sketchfab based on query and optional filters"""
    try:
        scene = bpy.context.scene
        api_key = getattr(scene, 'blender_auto_mcp_sketchfab_api_key', '')
        if not api_key:
            return {"error": "Sketchfab API key is not configured"}
            
        # Build search parameters with exact fields from Sketchfab API docs
        params = {
            "type": "models",
            "q": query,
            "count": count,
            "downloadable": downloadable,
            "archives_flavours": False
        }
        
        if categories:
            params["categories"] = categories
            
        # Make API request to Sketchfab search endpoint
        # The proper format according to Sketchfab API docs for API key auth
        headers = {
            "Authorization": f"Token {api_key}"
        }
        
        
        # Use the search endpoint as specified in the API documentation
        response = requests.get(
            "https://api.sketchfab.com/v3/search",
            headers=headers,
            params=params,
            timeout=30  # Add timeout of 30 seconds
        )
        
        if response.status_code == 401:
            return {"error": "Authentication failed (401). Check your API key."}
            
        if response.status_code != 200:
            return {"error": f"API request failed with status code {response.status_code}"}
            
        response_data = response.json()
        
        # Safety check on the response structure
        if response_data is None:
            return {"error": "Received empty response from Sketchfab API"}
            
        # Handle 'results' potentially missing from response
        results = response_data.get("results", [])
        if not isinstance(results, list):
            return {"error": f"Unexpected response format from Sketchfab API: {response_data}"}
            
        return response_data
    
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Check your internet connection."}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def download_sketchfab_model(server_instance, uid):
    """Download a model from Sketchfab by its UID"""
    try:
        scene = bpy.context.scene
        api_key = getattr(scene, 'blender_auto_mcp_sketchfab_api_key', '')
        if not api_key:
            return {"error": "Sketchfab API key is not configured"}
            
        # Use proper authorization header for API key auth
        headers = {
            "Authorization": f"Token {api_key}"
        }
        
        # Request download URL using the exact endpoint from the documentation
        download_endpoint = f"https://api.sketchfab.com/v3/models/{uid}/download"
        
        response = requests.get(
            download_endpoint,
            headers=headers,
            timeout=30  # Add timeout of 30 seconds
        )
        
        if response.status_code == 401:
            return {"error": "Authentication failed (401). Check your API key."}
            
        if response.status_code != 200:
            return {"error": f"Download request failed with status code {response.status_code}"}
            
        data = response.json()
        
        # Safety check for None data
        if data is None:
            return {"error": "Received empty response from Sketchfab API for download request"}
            
        # Extract download URL with safety checks
        gltf_data = data.get("gltf")
        if not gltf_data:
            return {"error": "No gltf download URL available for this model. Response: " + str(data)}
            
        download_url = gltf_data.get("url")
        if not download_url:
            return {"error": "No download URL available for this model. Make sure the model is downloadable and you have access."}
            
        # Download the model (already has timeout)
        model_response = requests.get(download_url, timeout=60)  # 60 second timeout
        
        if model_response.status_code != 200:
            return {"error": f"Model download failed with status code {model_response.status_code}"}
            
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        zip_file_path = os.path.join(temp_dir, f"{uid}.zip")
        
        with open(zip_file_path, "wb") as f:
            f.write(model_response.content)
            
        # Extract the zip file with enhanced security
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # More secure zip slip prevention
            for file_info in zip_ref.infolist():
                # Get the path of the file
                file_path = file_info.filename
                
                # Convert directory separators to the current OS style
                # This handles both / and \ in zip entries
                target_path = os.path.join(temp_dir, os.path.normpath(file_path))
                
                # Get absolute paths for comparison
                abs_temp_dir = os.path.abspath(temp_dir)
                abs_target_path = os.path.abspath(target_path)
                
                # Ensure the normalized path doesn't escape the target directory
                if not abs_target_path.startswith(abs_temp_dir):
                    with suppress(Exception):
                        shutil.rmtree(temp_dir)
                    return {"error": "Security issue: Zip contains files with path traversal attempt"}
                
                # Additional explicit check for directory traversal
                if ".." in file_path:
                    with suppress(Exception):
                        shutil.rmtree(temp_dir)
                    return {"error": "Security issue: Zip contains files with directory traversal sequence"}
            
            # If all files passed security checks, extract them
            zip_ref.extractall(temp_dir)
            
        # Find the main glTF file
        gltf_files = [f for f in os.listdir(temp_dir) if f.endswith('.gltf') or f.endswith('.glb')]
        
        if not gltf_files:
            with suppress(Exception):
                shutil.rmtree(temp_dir)
            return {"error": "No glTF file found in the downloaded model"}
            
        main_file = os.path.join(temp_dir, gltf_files[0])
        
        # Import the model
        bpy.ops.import_scene.gltf(filepath=main_file)
        
        # Get the names of imported objects
        imported_objects = [obj.name for obj in bpy.context.selected_objects]
        
        # Clean up temporary files
        with suppress(Exception):
            shutil.rmtree(temp_dir)
        
        return {
            "success": True,
            "message": "Model imported successfully",
            "imported_objects": imported_objects
        }
    
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Check your internet connection and try again with a simpler model."}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response from Sketchfab API: {str(e)}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Failed to download model: {str(e)}"}


# Handler dictionary factories
def get_polyhaven_handlers(server_instance):
    """Return PolyHaven handler dictionary"""
    return {
        "search_polyhaven_assets": lambda **kwargs: search_polyhaven_assets(server_instance, **kwargs),
        "download_polyhaven_asset": lambda **kwargs: download_polyhaven_asset(server_instance, **kwargs),
        "set_texture": lambda **kwargs: set_texture(server_instance, **kwargs),
    }


def get_hyper3d_handlers(server_instance):
    """Return Hyper3D/Rodin handler dictionary"""
    return {
        "create_rodin_job": lambda **kwargs: create_rodin_job(server_instance, **kwargs),
        "poll_rodin_job_status": lambda **kwargs: poll_rodin_job_status(server_instance, **kwargs),
        "import_generated_asset": lambda **kwargs: import_generated_asset(server_instance, **kwargs),
        "create_rodin_job_main_site": lambda **kwargs: create_rodin_job_main_site(server_instance, **kwargs),
        "create_rodin_job_fal_ai": lambda **kwargs: create_rodin_job_fal_ai(server_instance, **kwargs),
        "poll_rodin_job_status_main_site": lambda **kwargs: poll_rodin_job_status_main_site(server_instance, **kwargs),
        "poll_rodin_job_status_fal_ai": lambda **kwargs: poll_rodin_job_status_fal_ai(server_instance, **kwargs),
        "import_generated_asset_main_site": lambda **kwargs: import_generated_asset_main_site(server_instance, **kwargs),
        "import_generated_asset_fal_ai": lambda **kwargs: import_generated_asset_fal_ai(server_instance, **kwargs),
    }


def get_sketchfab_handlers(server_instance):
    """Return Sketchfab handler dictionary"""
    return {
        "search_sketchfab_models": lambda **kwargs: search_sketchfab_models(server_instance, **kwargs),
        "download_sketchfab_model": lambda **kwargs: download_sketchfab_model(server_instance, **kwargs),
    }