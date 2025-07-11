We need to implement a cli interface for users to easily operate this plugin, with the following features. use python package `click` to implement this.

- after user `pip install blender-remote`, he will have a CLI tool `blender-remote-cli` available in his python environment, directly callable in terminal

- `blender-remote-cli init <blender_executable_path>`, will record the <blender_executable_path> in `~/.config/blender-remote/bld-remote-config.yaml`, like the followings. The CLI will automatically find relevant paths and dirs, and print them to screen. If some path is not found, as user for it. Support this with `blender>=4.0` is OK, lower version is not supported, and raise error. By default calling `init` will recreate the config file and override everything, but user can `init --backup` to create `bld-remote-config.yaml.bak` automatically (override previous backup).

```yaml
blender:
    version: <auto found blender version>
    exec_path: <blender_executable_path>
    root_dir: <root dir of blender>
    plugin_dir: <plugin dir of blender>

mcp_service:
    # port used when starting blender with `blender-remote-cli` without specifying port
    default_port: <port of `BLD_Remote_MCP`, default=6688>

    # control logging level of `BLD_Remote_MCP`, default is INFO, same as `BLD_REMOTE_LOG_LEVEL`, case insensitive
    log_level: <log level of `BLD_Remote_MCP`, default=INFO>
```

- The `bld-remote-config.yaml` must exist for subcommands to work, otherwise raise error, except for `init` subcommand which will create that file if not exist.

- `blender-remote-cli install`, automatically install the addon to the blender, if already installed then override it. To do this, refer to `context/hints/howto-install-addon-blender.md`. If failed to install, raise error and let user knows.

- `blender-remote-cli config set mcp_service.default_port=xxx`, change `mcp_service.default_port` in config, likewise for everything else. If blender path or dir are changed, it is up to the user to guarantee consistency.

- just like the `config set`, user can use `config get` to get parameters, or just use `config get` without additional arguments to get all config

- `blender-remote-cli start`, start blender with `BLD_Remote_MCP` automatically started, using the `mcp_service.default_port` as the port, in GUI mode.
- - this command itself will block, and direct all blender console output to its `stdout` or `stderr`
- - `start --background` will start blender in background mode, the CLI is responsible to generate startup python code to be executed with `blender --background` so that blender does not immediately exit.
- - `start --pre-file=<user-script.py>` will prepend the user script as source code to the automatically generated startup code, so that user can do something before our startup script (empty in GUI mode). Note that as such, the `user-script.py` cannot accept arguments.
- - `start --pre-code="user-python-code"` is like the above, but the user specified stuff is now presented as source code. Note that, this conficts with `--pre-file` options
- - `start [OPTIONS] -- (arguments to blender)`, will pass other arguments to blender
- - `start --port=xxx` will override the default port to start `BLD_Remote_MCP`

- - `start --scene=<scene.blend>` will open the specified scene file in Blender (see `context/hints/howto-start-blender-with-scene.md` for details)
- - `start --log-level=<log_level>` will set the logging level for `BLD_Remote_MCP`, overriding the default in the config file. Valid values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive).
