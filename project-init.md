create a github repo:
# Blender Remote Project

- its name is `blender-remote`
- description: allowing remote control blender with python and MCP server, intended to be installed as `pip install blender-remote`
- this repo will be published to pypi, so create proper structure, we expect 
- it will has several parts, break into subdirs
- - `blender_addon`, multiple blender addons inside, intended to be installed into blender as plugin. These addons will create multiple non-stop services inside blender, which receive commands and execute them.
- - `blender_remote`, remote control code in python, used outside of blender environment, connect to blender addon to control blender, usage is like `import blender_remote.xxxx`
- the project contains python scripts as cli tools, create dir for these using the best practices
- create `README.md` with proper introduction
- when developing, the python environment is managed by `pixi`

## Context Dir

the `context` dir contains many reference materials for AI coding assistant, including these subdirs
- `hints`, hints to do various programming tasks, usually some tutorials collected online
- `summaries`, summary of experience, like project details, how to do some complext tasks after many rounds of talks, how to use specific tools or libraries, etc.
- `tasks`, prompts about various task defined by human, to be completed by AI coding assistant, each task has its own subdir
- `logs`, various logs of on going operations, used as a memory for the AI assistant
- `refcode`, reference code repositories, included inside this project as git submodules, mainly for the AI assistants to understand inner workings of some libraries
- `tools`, AI-created scripts to help it deal with problems in a more efficient way, usually developed based on past conversations, and to save tokens in the future
