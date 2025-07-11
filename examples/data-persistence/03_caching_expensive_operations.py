#!/usr/bin/env python3
"""
Caching Expensive Operations Example

Shows how to cache expensive calculations to avoid recomputation.
Simulates expensive mesh operations that benefit from caching.
"""

import json
import socket
import sys
import time


def send_command(command_type, params=None):
    """Send command to BLD Remote MCP service."""
    if params is None:
        params = {}
    
    command = {"type": command_type, "params": params}
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 6688))
        sock.send(json.dumps(command).encode())
        response = json.loads(sock.recv(8192).decode())
        return response
    finally:
        sock.close()


def expensive_mesh_analysis():
    """Perform expensive mesh analysis with caching."""
    print("🔍 Performing mesh analysis...")
    
    # Check if analysis is already cached
    response = send_command("get_persist_data", {"key": "mesh_analysis_cache"})
    
    if response.get('status') == 'success' and response['result']['found']:
        cached_data = response['result']['data']
        print("   📋 Found cached analysis results!")
        print(f"   Cache timestamp: {cached_data['timestamp']}")
        print(f"   Objects analyzed: {len(cached_data['results'])}")
        return cached_data['results']
    
    print("   ⚙️  No cache found, performing analysis...")
    
    # Perform expensive analysis
    code = """
import bpy
import bld_remote
import time
import mathutils

# Create test objects if scene is empty
if len(bpy.context.scene.objects) < 3:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    # Create various mesh objects
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    bpy.ops.mesh.primitive_sphere_add(location=(2, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(location=(4, 0, 0))

start_time = time.time()

# Perform expensive analysis on each mesh
analysis_results = {}
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        mesh = obj.data
        
        # Simulate expensive calculations
        time.sleep(0.5)  # Simulate processing time
        
        # Calculate various mesh properties
        vertices = len(mesh.vertices)
        edges = len(mesh.edges)
        faces = len(mesh.polygons)
        
        # Calculate bounding box volume
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_coords = [min(corner[i] for corner in bbox_corners) for i in range(3)]
        max_coords = [max(corner[i] for corner in bbox_corners) for i in range(3)]
        volume = (max_coords[0] - min_coords[0]) * (max_coords[1] - min_coords[1]) * (max_coords[2] - min_coords[2])
        
        # Calculate surface area (approximation)
        surface_area = sum(poly.area for poly in mesh.polygons)
        
        analysis_results[obj.name] = {
            "vertices": vertices,
            "edges": edges,
            "faces": faces,
            "volume": round(volume, 3),
            "surface_area": round(surface_area, 3),
            "complexity_score": vertices + faces * 2
        }

processing_time = time.time() - start_time

# Cache the results
cache_data = {
    "results": analysis_results,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "processing_time": round(processing_time, 2),
    "objects_count": len(analysis_results)
}

bld_remote.persist.put_data("mesh_analysis_cache", cache_data)

print(f"Analysis complete: {len(analysis_results)} objects in {processing_time:.2f}s")
for name, data in analysis_results.items():
    print(f"  {name}: {data['vertices']} vertices, complexity: {data['complexity_score']}")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Analysis failed: {response}")
    
    # Get the cached results
    response = send_command("get_persist_data", {"key": "mesh_analysis_cache"})
    if response.get('status') == 'success' and response['result']['found']:
        cached_data = response['result']['data']
        print(f"   ✅ Analysis cached ({cached_data['processing_time']}s)")
        return cached_data['results']
    else:
        raise Exception("Failed to cache analysis results")


def expensive_material_optimization():
    """Perform expensive material optimization with caching."""
    print("🎨 Optimizing materials...")
    
    # Check cache
    response = send_command("get_persist_data", {"key": "material_optimization_cache"})
    
    if response.get('status') == 'success' and response['result']['found']:
        cached_data = response['result']['data']
        print("   📋 Found cached optimization results!")
        print(f"   Optimizations: {len(cached_data['optimizations'])}")
        return cached_data['optimizations']
    
    print("   ⚙️  No cache found, performing optimization...")
    
    code = """
import bpy
import bld_remote
import time

start_time = time.time()

# Ensure we have some materials
if len(bpy.data.materials) == 0:
    # Create sample materials
    for i in range(3):
        mat = bpy.data.materials.new(name=f"Material_{i:03d}")
        mat.use_nodes = True
        # Add some complexity
        mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

optimizations = {}
for material in bpy.data.materials:
    # Simulate expensive optimization
    time.sleep(0.3)
    
    # Mock optimization analysis
    node_count = len(material.node_tree.nodes) if material.use_nodes else 0
    optimization_score = max(0, 100 - node_count * 5)
    
    suggestions = []
    if node_count > 10:
        suggestions.append("Reduce node complexity")
    if not material.use_nodes:
        suggestions.append("Enable node-based materials")
    if node_count < 3:
        suggestions.append("Material could be more detailed")
    
    optimizations[material.name] = {
        "node_count": node_count,
        "optimization_score": optimization_score,
        "suggestions": suggestions,
        "estimated_performance_gain": f"{optimization_score}%"
    }

processing_time = time.time() - start_time

# Cache the optimization results
cache_data = {
    "optimizations": optimizations,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "processing_time": round(processing_time, 2),
    "materials_count": len(optimizations)
}

bld_remote.persist.put_data("material_optimization_cache", cache_data)

print(f"Optimization complete: {len(optimizations)} materials in {processing_time:.2f}s")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Optimization failed: {response}")
    
    # Get cached results
    response = send_command("get_persist_data", {"key": "material_optimization_cache"})
    if response.get('status') == 'success' and response['result']['found']:
        cached_data = response['result']['data']
        print(f"   ✅ Optimization cached ({cached_data['processing_time']}s)")
        return cached_data['optimizations']
    else:
        raise Exception("Failed to cache optimization results")


def generate_report():
    """Generate a comprehensive report using cached data."""
    print("📊 Generating comprehensive report...")
    
    # Get both cached analyses
    mesh_response = send_command("get_persist_data", {"key": "mesh_analysis_cache"})
    material_response = send_command("get_persist_data", {"key": "material_optimization_cache"})
    
    if not (mesh_response.get('status') == 'success' and mesh_response['result']['found']):
        raise Exception("Mesh analysis cache not found")
    
    if not (material_response.get('status') == 'success' and material_response['result']['found']):
        raise Exception("Material optimization cache not found")
    
    mesh_data = mesh_response['result']['data']
    material_data = material_response['result']['data']
    
    # Generate report
    code = f"""
import bld_remote

# Get cached data
mesh_cache = bld_remote.persist.get_data("mesh_analysis_cache")
material_cache = bld_remote.persist.get_data("material_optimization_cache")

# Generate comprehensive report
report = {{
    "scene_summary": {{
        "objects_analyzed": mesh_cache["objects_count"],
        "materials_optimized": material_cache["materials_count"],
        "total_processing_time": mesh_cache["processing_time"] + material_cache["processing_time"]
    }},
    "mesh_analysis": mesh_cache["results"],
    "material_optimization": material_cache["optimizations"],
    "recommendations": [],
    "generated_at": mesh_cache["timestamp"]
}}

# Add intelligent recommendations based on cached data
total_vertices = sum(obj["vertices"] for obj in mesh_cache["results"].values())
if total_vertices > 10000:
    report["recommendations"].append("Consider using LOD (Level of Detail) for high-poly objects")

low_optimization_materials = [
    name for name, data in material_cache["optimizations"].items() 
    if data["optimization_score"] < 50
]
if low_optimization_materials:
    report["recommendations"].append(f"Optimize materials: {{', '.join(low_optimization_materials)}}")

# Cache the final report
bld_remote.persist.put_data("comprehensive_report", report)

print("Report generated successfully!")
print(f"Scene: {{report['scene_summary']['objects_analyzed']}} objects, {{report['scene_summary']['materials_optimized']}} materials")
print(f"Total analysis time: {{report['scene_summary']['total_processing_time']:.2f}}s")
print(f"Recommendations: {{len(report['recommendations'])}}")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Report generation failed: {response}")
    
    # Get the final report
    response = send_command("get_persist_data", {"key": "comprehensive_report"})
    if response.get('status') == 'success' and response['result']['found']:
        report = response['result']['data']
        print("   ✅ Report generated and cached")
        print(f"   Objects: {report['scene_summary']['objects_analyzed']}")
        print(f"   Materials: {report['scene_summary']['materials_optimized']}")
        print(f"   Total time: {report['scene_summary']['total_processing_time']:.2f}s")
        if report['recommendations']:
            print("   Recommendations:")
            for rec in report['recommendations']:
                print(f"     • {rec}")
        return report
    else:
        raise Exception("Failed to get generated report")


def clear_cache():
    """Clear all cached data."""
    print("🧹 Clearing cache...")
    
    cache_keys = [
        "mesh_analysis_cache",
        "material_optimization_cache", 
        "comprehensive_report"
    ]
    
    for key in cache_keys:
        response = send_command("remove_persist_data", {"key": key})
        if response.get('status') == 'success':
            removed = response['result']['removed']
            print(f"   {key}: {'✅ removed' if removed else '⚠️  not found'}")


def main():
    print("🚀 Caching Expensive Operations Example")
    print("=" * 50)
    print("This example demonstrates caching expensive calculations:")
    print("• Mesh analysis (vertices, faces, complexity)")
    print("• Material optimization recommendations")
    print("• Comprehensive report generation")
    print()
    
    try:
        # First run - should compute everything
        print("🔄 First run (no cache):")
        start_time = time.time()
        
        mesh_results = expensive_mesh_analysis()
        print()
        
        material_results = expensive_material_optimization()
        print()
        
        report = generate_report()
        
        first_run_time = time.time() - start_time
        print(f"\n⏱️  First run total time: {first_run_time:.2f}s")
        print()
        
        # Second run - should use cache
        print("🔄 Second run (with cache):")
        start_time = time.time()
        
        mesh_results = expensive_mesh_analysis()
        print()
        
        material_results = expensive_material_optimization()
        print()
        
        report = generate_report()
        
        second_run_time = time.time() - start_time
        print(f"\n⏱️  Second run total time: {second_run_time:.2f}s")
        
        speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
        print(f"🚀 Speedup: {speedup:.1f}x faster with caching!")
        print()
        
        clear_cache()
        
        print("✅ Caching example completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        clear_cache()  # Clean up on failure
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())