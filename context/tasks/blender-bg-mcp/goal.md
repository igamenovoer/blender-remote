# Minimal Blender MCP Service With Background Running Support

We are developing a blender plugin that supports MCP (Model Context Protocol) in blender, so that it can be controlled by LLM.

The goal is to develop blender mcp server (inspired by `blender-mcp` in `context/refcode/blender-mcp`), which supports startup control with env variables, running without GUI so that it works in `blender --background` mode, and also has GUI when blender is started with GUI. Compared to the `blender-mcp`, this one is minimal, will NOT include access functions to 3rd party 3d model repositories (`sketchfab`, `Hyper3D`, `Poly Haven`, etc).

## Design

The plugin

## Feature