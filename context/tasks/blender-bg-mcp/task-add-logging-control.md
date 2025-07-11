✅ **COMPLETED** - Add logging control to BLD_Remote_MCP

for `BLD_Remote_MCP` add an environment variable for logging verbosity control:
- `BLD_REMOTE_LOG_LEVEL` can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive) to control the logging level, just like the standard Python logging module, if not specified or empty, default is `INFO`.

## Implementation Status

✅ **COMPLETED** (2025-07-11)
- Added `BLD_REMOTE_LOG_LEVEL` environment variable support
- Implemented standard logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Case-insensitive with INFO as default level
- Updated `utils.py` with level filtering and new `log_critical()` function
- Integrated with CLI `--log-level` option for easy control
- Comprehensive test suite and documentation added
- Git commit: `0d79d5b`

### Usage Examples:
```bash
# Set via environment variable
export BLD_REMOTE_LOG_LEVEL=DEBUG
blender-remote-cli start

# Set via CLI option (overrides environment)
blender-remote-cli start --log-level WARNING

# Set via config file
blender-remote-cli config set mcp_service.log_level=ERROR
```

### Technical Implementation:
- Environment variable: `BLD_REMOTE_LOG_LEVEL`
- Location: `blender_addon/bld_remote_mcp/utils.py`
- Function: `_get_log_level()` with level mapping
- Integration: CLI sets environment variable for Blender process