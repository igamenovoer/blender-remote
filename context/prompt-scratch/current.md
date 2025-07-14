# This file is for random prompts, temporary stuff

**DO NOT READ THIS FILE UNLESS YOU ARE TOLD TO DO**
**It contains many outdated and temporary information**

### 20250714

we checked that modal operator does not work properly, now we change the approach, we will NOT use `bpy.app.timers.register()` to register a function in background mode, instead, we do the following:
- create a background plugin like `blender_addon/bld_remote_mcp/__init__.py`, which pure python class plugin, runs in background mode, and does not depend on Blender's GUI.
- the new plugin still has the same functionality as the `blender_addon/simple-tcp-executor`, but it does not use `bpy.app.timers.register()` to register a function, instead, it uses a simple TCP server to listen for commands, and execute them in Blender's context. To do so, it has a `step()` method, which is called periodically by the main thread, and it will pull commands from the queue and just execute them, without worrying about which thread is running the code, let the outer layer handle the threading issues.
- when `step()` is called, it will just pull all commands from the queue, and execute them one by one. When the callables are pushed into queue, they are pushed with a callback function, which will be called when the command is finished, with the result of the command. The original socket handling thread will wait fo this callback (probably it encapsulates some thread synchronization mechanism), and return the result to the client.

Before we go with this approach, we backup the current implementation of `simple-tcp-executor` by copying its `__init__.py` into `as_modal_operator.py`, and then we will implement the new plugin in `blender_addon/simple-tcp-executor/__init__.py`.

---

we now need to find out the pattern of how to execute code in Blender's context, and return the result back to the client, in both GUI mode and background mode, using modal operator and manages event loop, first let's try the `blender_addon/simple-tcp-executor`, install it to the blender and see if works. Note that this plugin does not directly work with `blender-remote-cli.py`, you need to extend it a bit, adding a `debug` subcommand:
- `debug install`, install the debug plugin to Blender, which is `blender_addon/simple-tcp-executor`
- `debug start`, start the debug plugin, in GUI mode
- `debug start --background`, start the debug plugin, in background mode, this will run Blender in background mode, and keep it alive, so that you can connect to it later.
- `debug start --port=xxx`, start the debug plugin, in background mode, and listen on the specified port, default to 7777, if not set, read from env variable `BLD_DEBUG_TCP_PORT`, if not set, use 7777 as default.

And then, we try to see if we can execute some code in Blender's context, and return the result back to the client, in both GUI mode and background mode. The code should be a valid Python code that can be executed in Blender's context, and return a result that can be serialized to JSON.