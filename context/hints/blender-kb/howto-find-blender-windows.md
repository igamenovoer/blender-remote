# How to Reliably Find Blender 4.x on Windows

This guide provides several methods to reliably locate the Blender 4.x installation directory and executable (`blender.exe`) on a Windows system. The methods are ordered from most to least reliable.

## 1. Using the Windows Registry (Most Reliable for Installed Versions)

For versions of Blender installed via the MSI installer, the installation path is stored in the Windows Registry. This is the most definitive way to find it.

1.  **Open Registry Editor**: Press `Win + R`, type `regedit`, and press Enter.
2.  **Navigate to the Uninstall Keys**: In the Registry Editor, navigate to the following key in the left-hand pane. This key contains information about most installed 64-bit applications.
    ```
    HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\
    ```
3.  **Find the Blender Entry**:
    *   Look for a key that starts with `{Blender Foundation...}` or similar. The exact name might vary.
    *   Click on each key and look at the values in the right-hand pane. You are looking for a `DisplayName` that says "Blender" and a `DisplayVersion` that matches the version you are looking for (e.g., 4.x).
    *   Once you find the correct Blender entry, look for the `InstallLocation` value. This will give you the path to the Blender installation directory.
    *   The executable will be at `<InstallLocation>\blender.exe`.

    A common registry key for Blender 4.1 might look like this:
    `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{06D12596-FE75-45E7-9B34-8246143C257A}`

    **Example `InstallLocation` value**: `C:\Program Files\Blender Foundation\Blender 4.1\`

## 2. Checking Default Installation Paths

If you can't find the registry key or are looking for a quick check, Blender is often installed in one of these default locations.

### Standard Installation (`.msi`)

*   `C:\Program Files\Blender Foundation\Blender <version>\`
    *   Example: `C:\Program Files\Blender Foundation\Blender 4.1\`

### Steam Installation

If you installed Blender through Steam, it will be in your Steam library folder.
*   `C:\Program Files (x86)\Steam\steamapps\common\Blender\`

### Microsoft Store Installation

Blender from the Microsoft Store is installed in a sandboxed WindowsApps folder, which is hidden and has restricted access.
*   The path is typically like: `C:\Program Files\WindowsApps\BlenderFoundation.Blender_...`
*   The executable path can often be found via the `where blender` command in a Command Prompt if it's in the system's PATH.

## 3. Using PowerShell to Automate the Search

You can use a PowerShell script to automate searching the registry. This is faster and less error-prone than manual searching.

```powershell
# PowerShell script to find Blender 4.x installations

$uninstall_paths = @(
    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
    "HKLM:\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
)

Get-ItemProperty $uninstall_paths | Where-Object {
    ($_.DisplayName -like "Blender*") -and ($_.DisplayVersion -like "4.*")
} | Select-Object DisplayName, DisplayVersion, InstallLocation
```

**How to use:**
1.  Open PowerShell.
2.  Copy and paste the script into the terminal and press Enter.
3.  The output will list the `DisplayName`, `DisplayVersion`, and `InstallLocation` for all found Blender 4.x versions.

## 4. Manual File Search (For Portable `.zip` Versions)

If you are using a portable version of Blender (from a `.zip` file), it won't be in the registry. In this case, you'll have to search for it.

*   Check common locations where you might have extracted it, such as `C:\blender\`, `D:\tools\blender\`, or your `Downloads` folder.
*   Use the Windows search feature in the Start Menu or File Explorer to search for `blender.exe`. This can be slow.

## 5. Using Python to Automate the Search

For developers, automating this search with Python can be very useful. The following script uses the `winreg` module to scan the Windows Registry for Blender 4.x installations.

> **Note**: The `winreg` module is part of the Python standard library on Windows, so no additional installation is required (`pip install winreg` is not needed).

```python
import winreg

def find_blender_4_in_registry():
    """
    Scans the Windows Registry to find installation paths for Blender 4.x.

    Returns:
        A list of paths to the installation directories.
    """
    uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    blender_paths = []

    for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for arch_key in [0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                with winreg.OpenKey(hkey, uninstall_key_path, 0, winreg.KEY_READ | arch_key) as uninstall_key:
                    for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        with winreg.OpenKey(uninstall_key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                if "blender" in display_name.lower() and display_version.startswith("4."):
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    if install_location:
                                        blender_paths.append(install_location)
                            except OSError:
                                continue
            except OSError:
                continue
    
    return list(set(blender_paths)) # Return unique paths

if __name__ == "__main__":
    found_paths = find_blender_4_in_registry()
    if found_paths:
        print("Found Blender 4.x installations at:")
        for path in found_paths:
            print(f"- {path}")
    else:
        print("No Blender 4.x installations found in the registry.")

```

### How to Use the Python Script

1.  Save the code above as a Python file (e.g., `find_blender.py`).
2.  Run it from a command prompt or terminal: `python find_blender.py`.
3.  The script will print the installation locations of any Blender 4.x versions it finds in the registry.

By following these methods, you can reliably locate your Blender 4.x installation on Windows, regardless of how it was installed.
