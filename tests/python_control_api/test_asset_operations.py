#!/usr/bin/env python3
"""
Test asset operations with BLD Remote MCP service.
"""

import sys
import os
import traceback

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    import blender_remote
    
    def test_asset_manager_creation():
        """Test creating asset manager."""
        print("Testing asset manager creation...")
        
        # Method 1: Create with existing client
        client = blender_remote.connect_to_blender(port=6688)
        asset_manager = blender_remote.create_asset_manager(client)
        print(f"Created asset manager with client: {asset_manager.client.host}:{asset_manager.client.port}")
        
        # Method 2: Create with auto-client
        asset_manager2 = blender_remote.create_asset_manager(port=6688)
        print(f"Created asset manager with auto-client: {asset_manager2.client.host}:{asset_manager2.client.port}")
        
        return True
    
    def test_list_asset_libraries():
        """Test listing asset libraries."""
        print("\nTesting asset library listing...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # List all asset libraries
        print("Listing asset libraries...")
        libraries = asset_manager.list_asset_libraries()
        print(f"Found {len(libraries)} asset libraries:")
        
        for lib in libraries:
            print(f"  - {lib.name}: {lib.path}")
            print(f"    Valid: {lib.is_valid}")
        
        return True
    
    def test_asset_library_validation():
        """Test validating asset libraries."""
        print("\nTesting asset library validation...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get first library for testing
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping validation test")
            return True
        
        test_lib = libraries[0]
        print(f"Testing library: {test_lib.name}")
        
        # Validate the library
        validation = asset_manager.validate_library(test_lib.name)
        print(f"Validation results: {validation}")
        
        return validation.get("valid", False) or not validation.get("exists", True)
    
    def test_list_library_catalogs():
        """Test listing library catalogs."""
        print("\nTesting library catalog listing...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get libraries
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping catalog test")
            return True
        
        # Test with first library
        test_lib = libraries[0]
        print(f"Testing catalogs for library: {test_lib.name}")
        
        # List catalogs
        catalogs = asset_manager.list_library_catalogs(test_lib.name)
        print(f"Catalog structure: {catalogs}")
        
        if catalogs:
            print(f"  Directories: {len(catalogs.get('directories', []))}")
            print(f"  Blend files: {len(catalogs.get('blend_files', []))}")
            print(f"  Summary: {catalogs.get('summary', {})}")
        
        return True
    
    def test_list_library_collections():
        """Test listing collections in libraries."""
        print("\nTesting library collection listing...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get libraries
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping collection test")
            return True
        
        # Test with first library
        test_lib = libraries[0]
        print(f"Testing collections for library: {test_lib.name}")
        
        # List collections
        collections = asset_manager.list_library_collections(test_lib.name)
        print(f"Found {len(collections)} collections:")
        
        for coll in collections[:5]:  # Show first 5
            print(f"  - {coll.name} in {coll.file_path}")
        
        if len(collections) > 5:
            print(f"  ... and {len(collections) - 5} more")
        
        return True
    
    def test_search_collections():
        """Test searching collections."""
        print("\nTesting collection search...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get libraries
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping search test")
            return True
        
        # Test with first library
        test_lib = libraries[0]
        print(f"Testing search in library: {test_lib.name}")
        
        # Search for collections (using common terms)
        search_terms = ["Collection", "default", "scene", "object"]
        
        for term in search_terms:
            results = asset_manager.search_collections(test_lib.name, term)
            print(f"Search '{term}': {len(results)} results")
            
            for result in results[:2]:  # Show first 2
                print(f"  - {result.name} in {result.file_path}")
        
        return True
    
    def test_list_blend_files():
        """Test listing blend files."""
        print("\nTesting blend file listing...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get libraries
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping blend file test")
            return True
        
        # Test with first library
        test_lib = libraries[0]
        print(f"Testing blend files for library: {test_lib.name}")
        
        # List blend files
        blend_files = asset_manager.list_blend_files(test_lib.name)
        print(f"Found {len(blend_files)} blend files:")
        
        for blend_file in blend_files[:5]:  # Show first 5
            print(f"  - {blend_file}")
        
        if len(blend_files) > 5:
            print(f"  ... and {len(blend_files) - 5} more")
        
        return True
    
    def test_asset_data_types():
        """Test asset data types and attrs functionality."""
        print("\nTesting asset data types...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # Get libraries
        libraries = asset_manager.list_asset_libraries()
        
        if libraries:
            lib = libraries[0]
            print(f"Testing AssetLibrary: {lib.name}")
            print(f"  Type: {type(lib)}")
            print(f"  Path: {lib.path}")
            print(f"  Valid: {lib.is_valid}")
            
            # Test collections
            collections = asset_manager.list_library_collections(lib.name)
            if collections:
                coll = collections[0]
                print(f"Testing AssetCollection: {coll.name}")
                print(f"  Type: {type(coll)}")
                print(f"  Library: {coll.library_name}")
                print(f"  File path: {coll.file_path}")
                print(f"  Objects: {coll.objects}")
        
        return True
    
    def test_get_specific_library():
        """Test getting specific library by name."""
        print("\nTesting get specific library...")
        
        asset_manager = blender_remote.create_asset_manager(port=6688)
        
        # List all libraries first
        libraries = asset_manager.list_asset_libraries()
        
        if not libraries:
            print("No asset libraries configured, skipping specific library test")
            return True
        
        # Get first library by name
        test_lib_name = libraries[0].name
        print(f"Testing get library by name: {test_lib_name}")
        
        specific_lib = asset_manager.get_asset_library(test_lib_name)
        
        if specific_lib:
            print(f"Found library: {specific_lib.name} at {specific_lib.path}")
            return True
        else:
            print("Library not found")
            return False
    
    def run_all_tests():
        """Run all asset operation tests."""
        print("=" * 60)
        print("BLD Remote MCP Asset Operations Tests")
        print("=" * 60)
        
        tests = [
            test_asset_manager_creation,
            test_list_asset_libraries,
            test_asset_library_validation,
            test_list_library_catalogs,
            test_list_library_collections,
            test_search_collections,
            test_list_blend_files,
            test_asset_data_types,
            test_get_specific_library
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                    print(f"✓ {test.__name__} PASSED")
                else:
                    print(f"✗ {test.__name__} FAILED")
            except Exception as e:
                print(f"✗ {test.__name__} ERROR: {str(e)}")
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print(f"Test Results: {passed}/{total} tests passed")
        print("=" * 60)
        
        return passed == total
    
    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run this script from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
    sys.exit(1)