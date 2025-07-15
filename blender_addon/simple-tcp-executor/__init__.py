bl_info = {
    "name": "Simple TCP Executor",
    "author": "Cline",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "location": "Background Mode",
    "description": "Executes Python code received over TCP using manual step() processing",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}

import bpy
import socket
import threading
import queue
import os
import sys
from typing import Callable, Any, Optional

# Debug logging to file
DEBUG_LOG_FILE = '/tmp/blender_debug.log'

def debug_log(message: str) -> None:
    """Write debug message to file and stdout"""
    with open(DEBUG_LOG_FILE, 'a') as f:
        f.write(f"{message}\n")
        f.flush()
    print(message)
    sys.stdout.flush()

# --- New Architecture Overview ---
# This plugin implements a pure Python class-based approach that doesn't rely on
# Blender's timer system or modal operators. Instead, it uses:
#
# 1. A TCPExecutor class that manages the TCP server and queue processing
# 2. A step() method that's called manually by the main thread to process the queue
# 3. A callback-based system for result handling with thread synchronization
# 4. Direct queue processing without depending on Blender's event system
#
# The architecture is:
# TCP Server Thread -> Queue -> step() Method -> Code Execution -> Callback -> Response

class ExecutionJob:
    """Represents a job to be executed with callback for result handling"""
    def __init__(self, code: str, callback: Callable[[Any], None]):
        self.code = code
        self.callback = callback
        self.result = None
        self.error = None
        self.completed = threading.Event()

class TCPExecutor:
    """Pure Python TCP executor that doesn't rely on Blender's timer system"""
    
    def __init__(self, host: str = 'localhost', port: int = 7777):
        self.host = host
        self.port = int(os.environ.get('BLD_DEBUG_TCP_PORT', port))
        self.execution_queue = queue.Queue()
        self.tcp_server = None
        self.running = False
        
        debug_log(f"TCP Executor initialized on {self.host}:{self.port}")
    
    def start(self) -> None:
        """Start the TCP server"""
        if self.running:
            debug_log("TCP Executor already running")
            return
            
        self.running = True
        self.tcp_server = TCPServerThread(self.host, self.port, self.execution_queue)
        self.tcp_server.start()
        debug_log("TCP Executor started")
    
    def stop(self) -> None:
        """Stop the TCP server"""
        if not self.running:
            return
            
        self.running = False
        if self.tcp_server:
            self.tcp_server.stop()
            self.tcp_server = None
        debug_log("TCP Executor stopped")
    
    def step(self) -> None:
        """Process all pending jobs in the queue - called manually by main thread"""
        if not self.running:
            return
            
        processed_count = 0
        
        # Process all jobs in the queue
        while not self.execution_queue.empty():
            try:
                job = self.execution_queue.get_nowait()
                processed_count += 1
                
                debug_log(f"Processing job {processed_count}: {repr(job.code[:50])}...")
                
                # Execute the code in the main thread (thread-safe for Blender)
                try:
                    exec_globals = {
                        'bpy': bpy,
                        'result': None  # Default result
                    }
                    
                    # Execute the code
                    exec(job.code, exec_globals)
                    
                    # Get the result
                    result = exec_globals.get('result', 'No result variable set.')
                    job.result = result
                    
                    debug_log(f"Job {processed_count} completed successfully: {repr(str(result)[:50])}")
                    
                except Exception as e:
                    job.error = str(e)
                    debug_log(f"Job {processed_count} failed: {e}")
                
                # Call the callback to notify the waiting thread
                try:
                    if job.error:
                        job.callback(f"Error: {job.error}")
                    else:
                        job.callback(job.result)
                    job.completed.set()
                except Exception as e:
                    debug_log(f"Callback error for job {processed_count}: {e}")
                    job.completed.set()
                
            except queue.Empty:
                break
            except Exception as e:
                debug_log(f"Error processing job: {e}")
        
        if processed_count > 0:
            debug_log(f"step() processed {processed_count} jobs")

class TCPServerThread(threading.Thread):
    """TCP server running in a separate thread"""
    
    def __init__(self, host: str, port: int, execution_queue: queue.Queue):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.execution_queue = execution_queue
        self.running = False
        self._server_socket = None
        
    def stop(self) -> None:
        """Stop the server thread gracefully"""
        self.running = False
        if self._server_socket:
            try:
                # Create a dummy connection to unblock the accept() call
                dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dummy_socket.connect((self.host, self.port))
                dummy_socket.close()
            except Exception as e:
                debug_log(f"TCP Server: Error during shutdown: {e}")
            
            self._server_socket.close()
        debug_log("TCP Server: Stopped")
    
    def run(self) -> None:
        """Main server loop"""
        self.running = True
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                self._server_socket = server_socket
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.host, self.port))
                server_socket.listen(5)
                
                debug_log(f"TCP Server: Listening on {self.host}:{self.port}")
                
                while self.running:
                    try:
                        conn, addr = server_socket.accept()
                        debug_log(f"TCP Server: Connected by {addr}")
                        
                        # Handle connection in a separate thread
                        handler = threading.Thread(
                            target=self._handle_connection,
                            args=(conn, addr),
                            daemon=True
                        )
                        handler.start()
                        
                    except OSError as e:
                        if self.running:
                            debug_log(f"TCP Server: Socket error: {e}")
                        break
                    except Exception as e:
                        if self.running:
                            debug_log(f"TCP Server: Error accepting connections: {e}")
                        
        except Exception as e:
            if self.running:
                debug_log(f"TCP Server: Failed to start: {e}")
        finally:
            self.running = False
            debug_log("TCP Server: Thread finished")
    
    def _handle_connection(self, conn: socket.socket, addr: tuple) -> None:
        """Handle a single client connection"""
        try:
            with conn:
                # Read all data from the client
                data_chunks = []
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data_chunks.append(chunk)
                
                # Decode the received code
                code_string = b"".join(data_chunks).decode('utf-8')
                debug_log(f"TCP Server: Received code from {addr}: {repr(code_string[:100])}")
                
                if code_string.strip():
                    # Create a result container and synchronization event
                    result_container = {}
                    result_event = threading.Event()
                    
                    def result_callback(result: Any) -> None:
                        """Callback function to receive the result"""
                        result_container['result'] = result
                        result_event.set()
                    
                    # Create and queue the job
                    job = ExecutionJob(code_string, result_callback)
                    self.execution_queue.put(job)
                    
                    debug_log(f"TCP Server: Job queued for {addr}, queue size: {self.execution_queue.qsize()}")
                    
                    # Wait for the result (with timeout)
                    timeout = 30  # 30 second timeout
                    if result_event.wait(timeout):
                        result = result_container.get('result', 'No result')
                        debug_log(f"TCP Server: Sending result to {addr}: {repr(str(result)[:100])}")
                        conn.sendall(str(result).encode('utf-8'))
                    else:
                        error_msg = f"Timeout: No response after {timeout} seconds"
                        debug_log(f"TCP Server: Timeout for {addr}")
                        conn.sendall(error_msg.encode('utf-8'))
                else:
                    debug_log(f"TCP Server: Empty code received from {addr}")
                    conn.sendall(b"Error: Empty code received")
                    
        except Exception as e:
            debug_log(f"TCP Server: Error handling connection from {addr}: {e}")

# Global TCP executor instance
_tcp_executor: Optional[TCPExecutor] = None

def get_tcp_executor() -> TCPExecutor:
    """Get the global TCP executor instance"""
    global _tcp_executor
    if _tcp_executor is None:
        port = int(os.environ.get('BLD_DEBUG_TCP_PORT', 7777))
        debug_log(f"DEBUG: Creating new TCP executor instance on port {port}")
        _tcp_executor = TCPExecutor(port=port)
    return _tcp_executor

def step() -> None:
    """Process pending jobs - called manually by main thread"""
    debug_log("DEBUG: step() function called from main thread")
    executor = get_tcp_executor()
    executor.step()

# --- Blender Plugin Registration ---

def register():
    """Register the plugin and start the TCP server"""
    debug_log(f"TCP Executor: Registering plugin, background mode: {bpy.app.background}")
    
    # Start the TCP executor
    executor = get_tcp_executor()
    executor.start()
    
    debug_log("TCP Executor: Plugin registered and TCP server started")

def unregister():
    """Unregister the plugin and stop the TCP server"""
    debug_log("TCP Executor: Unregistering plugin")
    
    # Stop the TCP executor
    executor = get_tcp_executor()
    executor.stop()
    
    debug_log("TCP Executor: Plugin unregistered and TCP server stopped")

# =============================================================================
# Module Interface - Make API available as simple_tcp_executor when imported
# =============================================================================

import sys

class SimpleTCPExecutorAPI:
    """API module for Simple TCP Executor."""
    
    @staticmethod
    def step():
        """Process pending jobs - called manually by main thread"""
        debug_log("DEBUG: step() function called from API module")
        executor = get_tcp_executor()
        executor.step()
    
    @staticmethod
    def get_executor():
        """Get the TCP executor instance"""
        return get_tcp_executor()
    
    @staticmethod
    def is_running():
        """Check if TCP executor is running"""
        executor = get_tcp_executor()
        return executor.running

# Register the API in sys.modules so it can be imported as 'import simple_tcp_executor'
sys.modules['simple_tcp_executor'] = SimpleTCPExecutorAPI()
debug_log("DEBUG: SimpleTCPExecutorAPI registered in sys.modules")

if __name__ == "__main__":
    register()