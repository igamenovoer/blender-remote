#!/usr/bin/env python3
"""
Health Monitoring Example

This example demonstrates monitoring the health and performance of the
BLD Remote MCP background service for production use.

Prerequisites:
- BLD Remote MCP service running
- Optional: logging facilities for production monitoring

Usage:
    python3 05_health_monitoring.py
    python3 05_health_monitoring.py --monitor --interval 5
"""

import sys
import os
import argparse
import time
import json
import threading
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    check_service_health, blender_connection, wait_for_service, 
    BldRemoteClient, print_status
)

class HealthMonitor:
    """Comprehensive health monitoring for BLD Remote MCP service."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 6688):
        self.host = host
        self.port = port
        self.monitoring = False
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'response_times': [],
            'errors': [],
            'start_time': None
        }
    
    def basic_health_check(self) -> dict:
        """Perform a basic health check."""
        print("🏥 Basic Health Check")
        print("-" * 30)
        
        start_time = time.time()
        health = check_service_health(self.host, self.port)
        response_time = time.time() - start_time
        
        print_status(health)
        print(f"Response time: {response_time:.3f} seconds")
        
        return {
            **health,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def detailed_health_check(self) -> dict:
        """Perform a detailed health check with multiple tests."""
        print("🔬 Detailed Health Check")
        print("-" * 30)
        
        start_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_health': 'unknown'
        }
        
        tests = [
            ('connection', self._test_connection),
            ('basic_command', self._test_basic_command),
            ('code_execution', self._test_code_execution),
            ('scene_access', self._test_scene_access),
            ('memory_usage', self._test_memory_usage),
            ('performance', self._test_performance)
        ]
        
        successful_tests = 0
        
        for test_name, test_func in tests:
            print(f"  Running {test_name} test...")
            try:
                test_result = test_func()
                results['tests'][test_name] = {
                    'status': 'pass' if test_result['success'] else 'fail',
                    'details': test_result,
                    'duration': test_result.get('duration', 0)
                }
                if test_result['success']:
                    successful_tests += 1
                    print(f"    ✓ {test_name}: PASS")
                else:
                    print(f"    ❌ {test_name}: FAIL - {test_result.get('error', 'Unknown error')}")
            except Exception as e:
                results['tests'][test_name] = {
                    'status': 'error',
                    'error': str(e),
                    'duration': 0
                }
                print(f"    ❌ {test_name}: ERROR - {e}")
        
        # Determine overall health
        total_tests = len(tests)
        success_rate = successful_tests / total_tests
        
        if success_rate >= 0.9:
            results['overall_health'] = 'healthy'
        elif success_rate >= 0.7:
            results['overall_health'] = 'degraded'
        else:
            results['overall_health'] = 'unhealthy'
        
        total_time = time.time() - start_time
        results['total_duration'] = total_time
        results['success_rate'] = success_rate
        
        print(f"\\n📊 Health Check Summary:")
        print(f"  • Overall Health: {results['overall_health'].upper()}")
        print(f"  • Tests Passed: {successful_tests}/{total_tests}")
        print(f"  • Success Rate: {success_rate:.1%}")
        print(f"  • Total Duration: {total_time:.2f}s")
        
        return results
    
    def _test_connection(self) -> dict:
        """Test basic connection capability."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=5.0) as client:
                duration = time.time() - start_time
                return {
                    'success': True,
                    'duration': duration,
                    'message': 'Connection successful'
                }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_basic_command(self) -> dict:
        """Test basic command sending."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=5.0) as client:
                response = client.send_message("Health check message")
                duration = time.time() - start_time
                
                if response.get('response') == 'OK':
                    return {
                        'success': True,
                        'duration': duration,
                        'response': response
                    }
                else:
                    return {
                        'success': False,
                        'duration': duration,
                        'error': f"Unexpected response: {response}"
                    }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_code_execution(self) -> dict:
        """Test Python code execution."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=10.0) as client:
                test_code = "import bpy; result = len(bpy.data.objects); print(f'Health check: {result} objects')"
                response = client.execute_code(test_code, "Health check code execution")
                duration = time.time() - start_time
                
                if response.get('response') == 'OK':
                    return {
                        'success': True,
                        'duration': duration,
                        'response': response
                    }
                else:
                    return {
                        'success': False,
                        'duration': duration,
                        'error': f"Code execution failed: {response}"
                    }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_scene_access(self) -> dict:
        """Test Blender scene access."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=10.0) as client:
                test_code = """
import bpy
scene = bpy.context.scene
result = {
    'scene_name': scene.name,
    'object_count': len(bpy.data.objects),
    'material_count': len(bpy.data.materials),
    'frame_current': scene.frame_current
}
print(f"Scene access test: {result}")
                """
                response = client.execute_code(test_code, "Scene access test")
                duration = time.time() - start_time
                
                if response.get('response') == 'OK':
                    return {
                        'success': True,
                        'duration': duration,
                        'scene_accessible': True
                    }
                else:
                    return {
                        'success': False,
                        'duration': duration,
                        'error': f"Scene access failed: {response}"
                    }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_memory_usage(self) -> dict:
        """Test memory usage information."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=10.0) as client:
                test_code = """
import bpy
import psutil
import os

# Get memory info
process = psutil.Process(os.getpid())
memory_info = process.memory_info()

result = {
    'memory_rss_mb': memory_info.rss / 1024 / 1024,
    'memory_vms_mb': memory_info.vms / 1024 / 1024,
    'cpu_percent': process.cpu_percent(),
    'blender_objects': len(bpy.data.objects),
    'blender_materials': len(bpy.data.materials)
}

print(f"Memory usage: {result}")
                """
                response = client.execute_code(test_code, "Memory usage test")
                duration = time.time() - start_time
                
                return {
                    'success': True,  # Always successful if we get here
                    'duration': duration,
                    'response': response
                }
                
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e),
                'note': 'psutil may not be available in Blender'
            }
    
    def _test_performance(self) -> dict:
        """Test performance with a simple workload."""
        start_time = time.time()
        try:
            with blender_connection(self.host, self.port, timeout=15.0) as client:
                test_code = """
import bpy
import time

start_time = time.time()

# Create and delete some objects to test performance
for i in range(10):
    bpy.ops.mesh.primitive_cube_add(location=(i, 0, 0))
    cube = bpy.context.active_object
    cube.name = f"PerfTest_{i}"

# Clean up
bpy.ops.object.select_all(action='SELECT')
for obj in bpy.context.selected_objects:
    if obj.name.startswith("PerfTest_"):
        bpy.data.objects.remove(obj, do_unlink=True)

duration = time.time() - start_time
print(f"Performance test: {duration:.3f}s for 10 create/delete operations")
                """
                response = client.execute_code(test_code, "Performance test")
                duration = time.time() - start_time
                
                if response.get('response') == 'OK':
                    return {
                        'success': True,
                        'duration': duration,
                        'performance_ok': duration < 10.0  # Should complete in under 10s
                    }
                else:
                    return {
                        'success': False,
                        'duration': duration,
                        'error': f"Performance test failed: {response}"
                    }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def continuous_monitoring(self, interval: int = 30, duration: int = 300):
        """
        Perform continuous monitoring for a specified duration.
        
        Args:
            interval: Seconds between checks
            duration: Total monitoring duration in seconds
        """
        print(f"🔄 Starting continuous monitoring (interval: {interval}s, duration: {duration}s)")
        print("-" * 60)
        
        self.monitoring = True
        self.stats['start_time'] = datetime.now()
        end_time = datetime.now() + timedelta(seconds=duration)
        
        try:
            while self.monitoring and datetime.now() < end_time:
                check_start = time.time()
                
                # Perform health check
                health = check_service_health(self.host, self.port)
                response_time = time.time() - check_start
                
                # Update statistics
                self.stats['total_checks'] += 1
                self.stats['response_times'].append(response_time)
                
                if health['responsive']:
                    self.stats['successful_checks'] += 1
                    status_icon = "✅"
                    status_text = "HEALTHY"
                else:
                    self.stats['failed_checks'] += 1
                    self.stats['errors'].append({
                        'timestamp': datetime.now().isoformat(),
                        'error': health.get('error', 'Unknown error')
                    })
                    status_icon = "❌"
                    status_text = "UNHEALTHY"
                
                # Display current status
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"{timestamp} {status_icon} {status_text} (response: {response_time:.3f}s)")
                
                # Show periodic summary
                if self.stats['total_checks'] % 10 == 0:
                    self._print_monitoring_summary()
                
                # Wait for next check
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\\n⏹️ Monitoring stopped by user")
        
        self.monitoring = False
        self._print_final_summary()
    
    def _print_monitoring_summary(self):
        """Print a summary of monitoring statistics."""
        uptime = datetime.now() - self.stats['start_time']
        avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
        availability = (self.stats['successful_checks'] / self.stats['total_checks']) * 100
        
        print(f"  📈 Summary: {self.stats['total_checks']} checks, "
              f"{availability:.1f}% availability, "
              f"avg response: {avg_response:.3f}s")
    
    def _print_final_summary(self):
        """Print final monitoring summary."""
        print("\\n📊 Final Monitoring Summary")
        print("=" * 40)
        
        uptime = datetime.now() - self.stats['start_time']
        total_checks = self.stats['total_checks']
        
        if total_checks > 0:
            availability = (self.stats['successful_checks'] / total_checks) * 100
            avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
            min_response = min(self.stats['response_times'])
            max_response = max(self.stats['response_times'])
            
            print(f"Monitoring Duration: {uptime}")
            print(f"Total Checks: {total_checks}")
            print(f"Successful: {self.stats['successful_checks']}")
            print(f"Failed: {self.stats['failed_checks']}")
            print(f"Availability: {availability:.2f}%")
            print(f"Response Times:")
            print(f"  • Average: {avg_response:.3f}s")
            print(f"  • Min: {min_response:.3f}s")
            print(f"  • Max: {max_response:.3f}s")
            
            if self.stats['errors']:
                print(f"\\nRecent Errors:")
                for error in self.stats['errors'][-5:]:  # Show last 5 errors
                    print(f"  • {error['timestamp']}: {error['error']}")
        else:
            print("No checks completed")

def main():
    parser = argparse.ArgumentParser(description='Monitor BLD Remote MCP service health')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Service host (default: 127.0.0.1)')
    parser.add_argument('--basic', action='store_true',
                        help='Run basic health check only')
    parser.add_argument('--monitor', action='store_true',
                        help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=30,
                        help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Monitoring duration in seconds (default: 300)')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Health Monitoring Example")
    print("=" * 50)
    
    monitor = HealthMonitor(args.host, args.port)
    
    if args.basic:
        # Basic health check only
        monitor.basic_health_check()
    elif args.monitor:
        # Continuous monitoring
        monitor.continuous_monitoring(args.interval, args.duration)
    else:
        # Default: detailed health check
        monitor.detailed_health_check()
        
        print("\\n💡 Monitoring Options:")
        print(f"  • Basic check: python3 {sys.argv[0]} --basic")
        print(f"  • Continuous: python3 {sys.argv[0]} --monitor --interval 10")
        print(f"  • Custom duration: python3 {sys.argv[0]} --monitor --duration 600")

if __name__ == '__main__':
    main()