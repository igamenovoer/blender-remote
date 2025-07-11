# Add logging control to BLD_Remote_MCP

for `BLD_Remote_MCP` add an environment variable for logging verbosity control:
- `BLD_REMOTE_LOG_LEVEL` can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (case insensitive) to control the logging level, just like the standard Python logging module, if not specified or empty, default is `INFO`.