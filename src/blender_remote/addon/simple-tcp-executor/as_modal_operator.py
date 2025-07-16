bl_info = {
    "name": "Simple TCP Executor",
    "author": "Cline",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > My Tab",
    "description": "Executes Python code received over TCP",
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
from concurrent.futures import Future

# Debug logging to file
DEBUG_LOG_FILE = '/tmp/blender_debug.log'

def debug_log(message):
    """Write debug message to file and stdout"""
    with open(DEBUG_LOG_FILE, 'a') as f:
        f.write(f"{message}\n")
        f.flush()
    print(message)
    sys.stdout.flush()

# --- Plugin Architecture Overview ---
# This plugin enables remote execution of Python code within Blender's main thread.
# It operates in two main modes: GUI and Background.
#
# 1. Multi-threading:
#    - A dedicated `TCPServerThread` runs a socket server on localhost:7777.
#      This thread listens for incoming TCP connections, receives Python code,
#      and is responsible for sending back the result.
#    - Blender's main thread is responsible for executing the received code.
#      This is crucial because the Blender Python API (bpy) is not thread-safe
#      and most operations must occur in the main thread.
#
# 2. Thread Communication:
#    - A thread-safe `queue.Queue` (`execution_queue`) is used to pass jobs
#      from the network thread to the main thread.
#    - A `concurrent.futures.Future` object is used to pass the result of the
#      executed code back from the main thread to the network thread. The
#      network thread blocks on `future.result()` until the main thread calls
#      `future.set_result()`.
#
# 3. Main Thread Integration (Event Loop):
#    - To avoid blocking the UI, the main thread cannot simply loop and wait for
#      jobs. It must periodically check the queue.
#    - In GUI mode, a `Modal Operator` is used. It adds a timer to Blender's
#      event loop, which periodically calls the queue processing logic.
#    - In Background mode (headless), a `Modal Operator` cannot be used. Instead,
#      `bpy.app.timers` is used to register a function that periodically
#      checks the queue. This achieves the same non-blocking execution.
#
# 4. Code Execution:
#    - The `exec()` function is used to run the received code string.
#    - The code is executed within a specific global context that includes `bpy`.
#    - The executed script is expected to place its return value in a variable
#      named `result`.
#
# 5. Configuration:
#    - The TCP port is configurable via the environment variable `BLD_DEBUG_TCP_PORT`.
#    - If the environment variable is not set, it defaults to 7777.

# --- Data shared between threads ---
execution_queue = queue.Queue()
"""
A thread-safe queue to pass jobs from the network thread to Blender's main thread.
Each job is a dictionary: {'code': <string>, 'future': <Future object>}
"""

# --- TCP Server running in a separate thread ---
class TCPServerThread(threading.Thread):
    """
    This thread runs a TCP socket server to listen for incoming code.
    It handles receiving data, putting jobs on the queue, and sending results back.
    """
    def __init__(self, host='localhost', port=7777):
        super().__init__(daemon=True)
        self.host = host
        self.port = int(os.environ.get('BLD_DEBUG_TCP_PORT', port))
        self.running = False
        self._server_socket = None

    def stop(self):
        """Stops the server thread gracefully."""
        self.running = False
        if self._server_socket:
            # Create a dummy connection to unblock the accept() call
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
            except Exception as e:
                print(f"TCP Server: Error during shutdown connection: {e}")
            self._server_socket.close()
        print("TCP Server: Stopped.")

    def run(self):
        """The main loop of the server thread."""
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                self._server_socket = s
                s.bind((self.host, self.port))
                s.listen()
                print(f"TCP Server: Listening on {self.host}:{self.port}")

                while self.running:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            print(f"TCP Server: Connected by {addr}")
                            data_chunks = []
                            while True:
                                chunk = conn.recv(1024)
                                if not chunk:
                                    break
                                data_chunks.append(chunk)
                            
                            code_string = b"".join(data_chunks).decode('utf-8')
                            debug_log(f"DEBUG: TCP Server received code: {repr(code_string)}")
                            if code_string:
                                future = Future()
                                debug_log(f"DEBUG: TCP Server putting job in queue, queue size before: {execution_queue.qsize()}")
                                execution_queue.put({'code': code_string, 'future': future})
                                debug_log(f"DEBUG: TCP Server job added to queue, queue size after: {execution_queue.qsize()}")
                                
                                # Block until the future is resolved by the main thread
                                debug_log("DEBUG: TCP Server waiting for result from main thread...")
                                result = future.result()
                                debug_log(f"DEBUG: TCP Server got result: {repr(result)}")
                                conn.sendall(str(result).encode('utf-8'))
                                debug_log("DEBUG: TCP Server sent result back to client")
                    except Exception as e:
                         if self.running:
                            print(f"TCP Server: Error during connection: {e}")
        except Exception as e:
            if self.running:
                print(f"TCP Server: Failed to start: {e}")
        finally:
            self.running = False
            print("TCP Server: Thread finished.")


# --- Core Logic ---
_tcp_thread = None

def process_execution_queue():
    """
    Checks the execution queue and runs the code in Blender's main thread.
    This function is designed to be called repeatedly by a timer.
    It returns the interval for the next call.
    """
    debug_log(f"DEBUG: process_execution_queue() called, queue size: {execution_queue.qsize()}")
    
    # Always return the next interval even if queue is empty
    next_interval = 0.1
    
    while not execution_queue.empty():
        try:
            job = execution_queue.get_nowait()
            code = job['code']
            future = job['future']
            
            print(f"Executor: Running code:\n---\n{code}\n---")
            
            try:
                # Prepare a context for the execution
                # Note: bpy.context might be limited in background mode
                exec_globals = {
                    'bpy': bpy,
                }
                # Execute the code
                exec(code, exec_globals)
                # Assume result is in a variable named 'result'
                result = exec_globals.get('result', 'No result variable set.')
                future.set_result(result)
            except Exception as e:
                print(f"Executor: Error executing code: {e}")
                future.set_result(f"Error: {e}")

        except queue.Empty:
            break # Exit loop if queue becomes empty
        except Exception as e:
            print(f"Executor: Error processing queue: {e}")
    
    debug_log(f"DEBUG: process_execution_queue() returning interval: {next_interval}")
    return next_interval # Reschedule for the next run

# --- GUI Mode Specifics ---
class TCPExecutorOperator(bpy.types.Operator):
    """
    A modal operator for running the executor in GUI mode.
    It sets up a timer that repeatedly calls the queue processing function.
    This allows the UI to remain responsive while checking for jobs.
    """
    bl_idname = "object.tcp_executor_operator"
    bl_label = "TCP Code Executor"

    _timer = None

    def modal(self, context, event):
        """The main loop of the modal operator."""
        global _tcp_thread
        debug_log(f"DEBUG: modal() called with event.type = {event.type}")
        
        if not _tcp_thread or not _tcp_thread.is_alive():
             print("TCP Executor: Server thread died. Operator is stopping.")
             self.cancel(context)
             return {'CANCELLED'}

        if event.type == 'TIMER':
            debug_log("DEBUG: TIMER event received in modal()")
            process_execution_queue()
        
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        """Called when the operator is first run."""
        global _tcp_thread
        if _tcp_thread is None or not _tcp_thread.is_alive():
            self.report({'ERROR'}, "TCP server not running. Please restart Blender and re-enable the addon.")
            return {'CANCELLED'}

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        print("TCP Executor: Modal operator started.")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        """Called when the operator is cancelled."""
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        print("TCP Executor: Modal operator stopped.")

class TCPExecutorPanel(bpy.types.Panel):
    """A UI panel in the 3D View sidebar to control the operator."""
    bl_label = "TCP Executor"
    bl_idname = "OBJECT_PT_tcp_executor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TCP Executor'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.tcp_executor_operator", text="Start/Stop Executor")

# --- Registration ---
classes = (
    TCPExecutorOperator,
    TCPExecutorPanel,
)

def register():
    """
    Registers the addon classes and starts the appropriate services.
    This function is called by Blender when the addon is enabled.
    It handles both GUI and background mode setup.
    """
    global _tcp_thread
    
    debug_log(f"DEBUG: register() called, background mode: {bpy.app.background}")

    # Start the TCP server thread, common for both modes
    if _tcp_thread is None or not _tcp_thread.is_alive():
        port = int(os.environ.get('BLD_DEBUG_TCP_PORT', 7777))
        debug_log(f"DEBUG: Starting TCP server on port {port}")
        _tcp_thread = TCPServerThread(port=port)
        _tcp_thread.start()
        debug_log("DEBUG: TCP server thread started")
    else:
        debug_log("DEBUG: TCP server thread already running")

    if bpy.app.background:
        # Background mode: use an application timer
        debug_log("TCP Executor: Running in background mode.")
        debug_log(f"DEBUG: Checking if timer is registered: {bpy.app.timers.is_registered(process_execution_queue)}")
        if not bpy.app.timers.is_registered(process_execution_queue):
            debug_log("DEBUG: Registering timer for process_execution_queue")
            
            # Test timer function
            def test_timer():
                debug_log("DEBUG: TEST TIMER CALLED!")
                return 0.5  # Call again in 0.5 seconds
            
            # Register both timers
            bpy.app.timers.register(test_timer, first_interval=0.5)
            bpy.app.timers.register(process_execution_queue, first_interval=1.0)
            debug_log(f"DEBUG: Timer registered? {bpy.app.timers.is_registered(process_execution_queue)}")
            debug_log(f"DEBUG: Test timer registered? {bpy.app.timers.is_registered(test_timer)}")
        else:
            debug_log("DEBUG: Timer already registered")
            # Test if timer is actually being called
            debug_log("DEBUG: Forcing a manual call to process_execution_queue()")
            try:
                result = process_execution_queue()
                debug_log(f"DEBUG: Manual call returned: {result}")
            except Exception as e:
                debug_log(f"DEBUG: Manual call failed: {e}")
        debug_log("TCP Executor: Queue processor registered with application timers.")
    else:
        # GUI mode: register the panel and operator
        print("TCP Executor: Running in GUI mode.")
        for cls in classes:
            bpy.utils.register_class(cls)
        print("TCP Executor: UI Panel and Operator registered.")
        
        # Auto-start the modal operator in GUI mode with a delay
        print("DEBUG: Auto-starting modal operator in GUI mode")
        
        def delayed_start():
            try:
                debug_log("DEBUG: Attempting to start modal operator...")
                bpy.ops.object.tcp_executor_operator('INVOKE_DEFAULT')
                debug_log("DEBUG: Modal operator started successfully")
                return None  # Don't reschedule
            except Exception as e:
                debug_log(f"DEBUG: Failed to start modal operator: {e}")
                return None  # Don't reschedule
        
        # Schedule the delayed start
        bpy.app.timers.register(delayed_start, first_interval=0.1)

def unregister():
    """
    Unregisters the addon classes and stops all running services.
    This function is called by Blender when the addon is disabled.
    """
    global _tcp_thread

    # Stop the thread when the addon is unregistered
    if _tcp_thread:
        _tcp_thread.stop()
        _tcp_thread = None
        print("TCP Executor: Server thread stopped.")

    if bpy.app.background:
        if bpy.app.timers.is_registered(process_execution_queue):
            bpy.app.timers.unregister(process_execution_queue)
            print("TCP Executor: Queue processor unregistered from application timers.")
    else:
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                # This can happen if the addon was not fully registered
                pass
        print("TCP Executor: UI Panel and Operator unregistered.")

if __name__ == "__main__":
    register()
