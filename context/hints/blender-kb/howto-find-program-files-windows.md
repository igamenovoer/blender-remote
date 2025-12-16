# How to Find the "Program Files" Directory on Windows

The `platformdirs` package is designed to find user-specific directories (e.g., user data, config, cache) and is not suitable for locating the system's "Program Files" directory.

The correct and standard method to find the "Program Files" directory on Windows is by using environment variables. Python's `os` module provides an easy way to access them.

## Python Implementation

You can use `os.getenv()` to read the `ProgramFiles` and `ProgramFiles(x86)` environment variables.

```python
import os

def find_program_files_windows():
    """
    Finds the 'Program Files' and 'Program Files (x86)' directories on Windows.
    """
    # This variable points to the primary Program Files directory.
    # On a 64-bit system, this is typically 'C:\Program Files'.
    # On a 32-bit system, it's also 'C:\Program Files'.
    program_files = os.getenv("ProgramFiles")
    print(f"Program Files: {program_files}")

    # This variable is only present on 64-bit systems and points to the
    # directory for 32-bit applications.
    # Typically 'C:\Program Files (x86)'.
    program_files_x86 = os.getenv("ProgramFiles(x86)")
    
    if program_files_x86:
        print(f"Program Files (x86): {program_files_x86}")
    else:
        print("Program Files (x86): Not found (likely a 32-bit system).")

if __name__ == "__main__":
    if os.name == 'nt':  # Check if the OS is Windows
        find_program_files_windows()
    else:
        print("This script is intended to be run on Windows.")
```

### Key Points:

-   **`os.getenv("ProgramFiles")`**: Retrieves the path to the main `Program Files` directory.
-   **`os.getenv("ProgramFiles(x86)")`**: Retrieves the path to the 32-bit `Program Files` directory on a 64-bit Windows installation. This will return `None` on a 32-bit system.
-   **`os.name == 'nt'`**: This is a reliable way to check if the code is running on a Windows system.
