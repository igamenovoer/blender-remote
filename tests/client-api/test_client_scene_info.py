#!/usr/bin/env python3
"""
BlenderMCPClient Scene Information Retrieval Testing

Tests scene information retrieval functionality including:
- get_scene_info() data structure validation
- get_object_info() for various object types
- test_connection() reliability
- get_status() service health monitoring

Based on: context/plans/blender-remote-client-test-plan.md
"""

import sys
import os
import json

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from blender_remote.client import BlenderMCPClient
    from blender_remote.exceptions import BlenderConnectionError
except ImportError as e:
    print(f"❌ Failed to import blender_remote modules: {e}")
    sys.exit(1)


class ClientSceneInfoTests:
    """Test BlenderMCPClient scene information retrieval functionality."""
    
    def __init__(self, host='127.0.0.1', port=6688):
        self.host = host
        self.port = port
        self.client = None
    
    def setup_client(self):
        """Setup client connection for testing."""
        try:
            print(f"🔌 Connecting to Blender service at {self.host}:{self.port}...")
            self.client = BlenderMCPClient(host=self.host, port=self.port)
            
            # Test connection
            status = self.client.test_connection()
            if not status:
                raise BlenderConnectionError("Connection test failed")
            
            print("✅ Client connection established")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup client: {e}")
            return False
    
    def test_get_scene_info(self):
        """Test get_scene_info data structure validation."""
        print("\n📋 Test: Get Scene Info")
        
        try:
            scene_info = self.client.get_scene_info()
            
            # Validate scene info structure
            required_fields = ["name", "objects"]  # Expected minimum fields
            validation_results = {}
            
            if isinstance(scene_info, dict):
                for field in required_fields:
                    validation_results[f"has_{field}"] = field in scene_info
                
                validation_results["is_dict"] = True
                validation_results["has_data"] = len(scene_info) > 0
            else:
                validation_results["is_dict"] = False
                validation_results["type"] = type(scene_info).__name__
            
            success = all(validation_results.get(f"has_{field}", False) for field in required_fields)
            
            print(f"    ✅ Scene info retrieved: {success}")
            return {
                "status": "success" if success else "partial",
                "scene_info": scene_info,
                "validation": validation_results
            }
            
        except Exception as e:
            print(f"    ❌ Get scene info failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_get_object_info(self):
        """Test get_object_info for various object types."""
        print("\n📋 Test: Get Object Info")
        
        try:
            # Test with default objects (usually Cube, Camera, Light)
            test_objects = ["Cube", "Camera", "Light"]
            results = {}
            
            for obj_name in test_objects:
                print(f"  Testing object: {obj_name}")
                try:
                    obj_info = self.client.get_object_info(obj_name)
                    
                    if isinstance(obj_info, dict) and len(obj_info) > 0:
                        results[obj_name] = {"status": "success", "info": obj_info}
                        print(f"    ✅ {obj_name}: Info retrieved")
                    else:
                        results[obj_name] = {"status": "empty", "info": obj_info}
                        print(f"    ⚠️ {obj_name}: Empty or invalid info")
                        
                except Exception as e:
                    results[obj_name] = {"status": "error", "error": str(e)}
                    print(f"    ❌ {obj_name}: Error - {e}")
            
            success_count = sum(1 for r in results.values() if r["status"] == "success")
            
            return {
                "status": "success" if success_count > 0 else "failed",
                "results": results,
                "success_count": success_count,
                "total_tested": len(test_objects)
            }
            
        except Exception as e:
            print(f"    ❌ Get object info test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_connection_reliability(self):
        """Test test_connection() reliability."""
        print("\n📋 Test: Connection Reliability")
        
        try:
            # Test connection multiple times
            connection_results = []
            test_count = 5
            
            for i in range(test_count):
                try:
                    result = self.client.test_connection()
                    connection_results.append({"attempt": i+1, "success": result})
                    print(f"  Connection test {i+1}: {'✅' if result else '❌'}")
                except Exception as e:
                    connection_results.append({"attempt": i+1, "success": False, "error": str(e)})
                    print(f"  Connection test {i+1}: ❌ Error - {e}")
            
            success_count = sum(1 for r in connection_results if r["success"])
            reliability = (success_count / test_count * 100)
            
            return {
                "status": "success" if reliability >= 80 else "failed",
                "results": connection_results,
                "reliability_percent": reliability,
                "successful_connections": success_count,
                "total_attempts": test_count
            }
            
        except Exception as e:
            print(f"    ❌ Connection reliability test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_get_status(self):
        """Test get_status() service health monitoring."""
        print("\n📋 Test: Get Status")
        
        try:
            status = self.client.get_status()
            
            # Validate status response
            validation_results = {
                "has_response": status is not None,
                "is_dict": isinstance(status, dict),
                "has_data": len(status) > 0 if isinstance(status, dict) else False
            }
            
            success = all(validation_results.values())
            
            print(f"    ✅ Status retrieved: {success}")
            return {
                "status": "success" if success else "partial",
                "service_status": status,
                "validation": validation_results
            }
            
        except Exception as e:
            print(f"    ❌ Get status failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def run_all_tests(self):
        """Run all scene information tests."""
        print("=" * 80)
        print("🧪 BlenderMCPClient Scene Information Tests")
        print("=" * 80)
        
        if not self.setup_client():
            return {"status": "setup_failed", "error": "Could not establish client connection"}
        
        tests = [
            ("Get Scene Info", self.test_get_scene_info),
            ("Get Object Info", self.test_get_object_info),
            ("Connection Reliability", self.test_connection_reliability),
            ("Get Status", self.test_get_status)
        ]
        
        results = {}
        passed_count = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                
                if result.get("status") == "success":
                    print(f"✅ {test_name}: PASSED")
                    passed_count += 1
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
        
        total_count = len(tests)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        overall_status = "PASS" if passed_count == total_count else "FAIL"
        
        print("\n" + "=" * 80)
        print("📊 Scene Information Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        print(f"📊 Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "individual_results": results,
            "passed_count": passed_count,
            "total_count": total_count
        }


def main():
    """Run scene information tests."""
    tester = ClientSceneInfoTests()
    results = tester.run_all_tests()
    
    exit_code = 0 if results.get("overall_status") == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)