#!/usr/bin/env python3
"""
Asset Management Example - Python Control API

This example demonstrates how to use BlenderAssetManager for browsing and
importing from Blender asset libraries.

Prerequisites:
- Blender running with BLD Remote MCP service on port 6688
- blender-remote package installed
- At least one asset library configured in Blender (optional)
"""

import blender_remote


def main():
    """Demonstrate asset management operations."""
    print("=== Asset Management Example ===")
    
    # Step 1: Create asset manager
    print("\n1. Creating asset manager...")
    try:
        asset_manager = blender_remote.create_asset_manager(port=6688)
        print("✓ Asset manager created")
    except blender_remote.BlenderConnectionError as e:
        print(f"✗ Failed to create asset manager: {e}")
        return
    
    # Step 2: List asset libraries
    print("\n2. Listing asset libraries...")
    libraries = asset_manager.list_asset_libraries()
    
    if not libraries:
        print("⚠ No asset libraries found")
        print("To add asset libraries in Blender:")
        print("  1. Go to Edit > Preferences")
        print("  2. Select File Paths tab")
        print("  3. Add Asset Libraries")
        print("\nContinuing with library management examples...")
        return
    
    print(f"Found {len(libraries)} asset libraries:")
    for i, lib in enumerate(libraries, 1):
        print(f"  {i}. {lib.name}")
        print(f"     Path: {lib.path}")
        print(f"     Valid: {lib.is_valid}")
    
    # Step 3: Validate libraries
    print("\n3. Validating asset libraries...")
    for lib in libraries:
        validation = asset_manager.validate_library(lib.name)
        print(f"\nLibrary '{lib.name}' validation:")
        print(f"  Valid: {validation.get('valid', False)}")
        print(f"  Exists: {validation.get('exists', False)}")
        print(f"  Accessible: {validation.get('accessible', False)}")
        print(f"  Blend files: {validation.get('blend_count', 0)}")
        print(f"  Collections: {validation.get('collection_count', 0)}")
    
    # Step 4: Work with first valid library
    valid_libraries = [lib for lib in libraries if lib.is_valid]
    if not valid_libraries:
        print("\n⚠ No valid libraries found")
        return
    
    test_lib = valid_libraries[0]
    print(f"\n4. Working with library: {test_lib.name}")
    
    # Step 5: List library catalogs
    print("\n5. Listing library catalogs...")
    catalogs = asset_manager.list_library_catalogs(test_lib.name)
    
    if catalogs:
        print(f"Library structure:")
        print(f"  Directories: {len(catalogs.get('directories', []))}")
        print(f"  Blend files: {len(catalogs.get('blend_files', []))}")
        print(f"  Total items: {catalogs.get('summary', {}).get('total_items', 0)}")
        
        # Show first few directories
        directories = catalogs.get('directories', [])
        if directories:
            print(f"\nFirst directories:")
            for dir_name in directories[:5]:
                print(f"    {dir_name}")
            if len(directories) > 5:
                print(f"    ... and {len(directories) - 5} more")
        
        # Show first few blend files
        blend_files = catalogs.get('blend_files', [])
        if blend_files:
            print(f"\nFirst blend files:")
            for file_name in blend_files[:5]:
                print(f"    {file_name}")
            if len(blend_files) > 5:
                print(f"    ... and {len(blend_files) - 5} more")
    
    # Step 6: List all blend files
    print("\n6. Listing all blend files...")
    all_blend_files = asset_manager.list_blend_files(test_lib.name)
    print(f"Found {len(all_blend_files)} blend files total")
    
    if all_blend_files:
        print("First 10 blend files:")
        for file_path in all_blend_files[:10]:
            print(f"    {file_path}")
        if len(all_blend_files) > 10:
            print(f"    ... and {len(all_blend_files) - 10} more")
    
    # Step 7: List collections
    print("\n7. Listing collections...")
    collections = asset_manager.list_library_collections(test_lib.name)
    print(f"Found {len(collections)} collections")
    
    if collections:
        print("First 10 collections:")
        for coll in collections[:10]:
            print(f"    {coll.name} in {coll.file_path}")
        if len(collections) > 10:
            print(f"    ... and {len(collections) - 10} more")
    
    # Step 8: Search collections
    print("\n8. Searching collections...")
    search_terms = ["Collection", "default", "scene", "object", "material"]
    
    for term in search_terms:
        results = asset_manager.search_collections(test_lib.name, term)
        if results:
            print(f"Search '{term}': {len(results)} results")
            for result in results[:3]:  # Show first 3 results
                print(f"    {result.name} in {result.file_path}")
            if len(results) > 3:
                print(f"    ... and {len(results) - 3} more")
        else:
            print(f"Search '{term}': No results")
    
    # Step 9: Get specific library
    print("\n9. Getting specific library...")
    specific_lib = asset_manager.get_asset_library(test_lib.name)
    if specific_lib:
        print(f"Retrieved library: {specific_lib.name}")
        print(f"    Path: {specific_lib.path}")
        print(f"    Valid: {specific_lib.is_valid}")
    
    # Step 10: Demonstrate collection import (if collections exist)
    print("\n10. Collection import demonstration...")
    if collections:
        first_collection = collections[0]
        print(f"Attempting to import: {first_collection.name}")
        print(f"    From file: {first_collection.file_path}")
        print(f"    In library: {first_collection.library_name}")
        
        try:
            success = asset_manager.import_collection(
                first_collection.library_name,
                first_collection.file_path,
                first_collection.name
            )
            
            if success:
                print("✓ Collection imported successfully")
                
                # Verify import by checking scene
                scene_manager = blender_remote.create_scene_manager(asset_manager.client)
                scene_info = scene_manager.get_scene_info()
                print(f"Scene now has {scene_info.object_count} objects")
                
            else:
                print("✗ Collection import failed")
                
        except Exception as e:
            print(f"✗ Import error: {e}")
    else:
        print("⚠ No collections available for import demonstration")
    
    # Step 11: Summary
    print("\n11. Summary...")
    print(f"Total libraries: {len(libraries)}")
    print(f"Valid libraries: {len(valid_libraries)}")
    if valid_libraries:
        print(f"Test library: {test_lib.name}")
        print(f"Collections found: {len(collections)}")
        print(f"Blend files found: {len(all_blend_files)}")
    
    print("\n=== Asset Management Example Complete ===")


if __name__ == "__main__":
    main()