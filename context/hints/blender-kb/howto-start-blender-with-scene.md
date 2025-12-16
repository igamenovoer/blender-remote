# How to Start Blender with a Scene File

This document explains how to open a `.blend` scene file when launching Blender from the command line.

## GUI Mode

To open a scene file and run Blender in its standard graphical user interface, pass the path to the `.blend` file as an argument to the Blender executable:

```bash
blender /path/to/your/scene.blend
```

If the `blender` command is not in your system's PATH, you'll need to use the full path to the executable. For example:

**Windows:**
```bash
"C:\Program Files\Blender Foundation\Blender\blender.exe" "C:\Users\user\Documents\my_scene.blend"
```

**macOS:**
```bash
/Applications/Blender.app/Contents/MacOS/blender /Users/user/Documents/my_scene.blend
```

**Linux:**
```bash
./blender /home/user/documents/my_scene.blend
```

## Background Mode

When using Blender in background mode, you must also provide a Python script (`--python <script.py>`) or use the Python console (`--python-console`) to prevent Blender from exiting immediately after startup.

To open a scene file in background mode, place the file path before the `--background` flag:

```bash
blender /path/to/your/scene.blend --background --python your_script.py
```
