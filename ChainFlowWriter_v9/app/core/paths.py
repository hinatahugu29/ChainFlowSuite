import os
import sys

def get_data_dir(app_name="ChainFlowWriter"):
    """
    Determines the data directory in a 'Portable-First' manner.
    1. Local: Tries to use 'snippets_data' in the executable's directory.
    2. Fallback: If local directory is not writable (e.g. Program Files), uses APPDATA.
    """
    # Get the directory of the executable or the script
    if getattr(sys, 'frozen', False):
        # PyInstaller bundled
        base_dir = os.path.dirname(sys.executable)
    else:
        # Script mode
        # Path depth: app/core/paths.py -> 3 levels up to root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    local_data_path = os.path.join(base_dir, "snippets_data")
    
    # Check if we can use the local directory (already exists OR we can create it)
    can_write_local = False
    if os.path.exists(local_data_path):
        if os.access(local_data_path, os.W_OK):
            can_write_local = True
    else:
        # Check if the parent directory is writable so we can create snippets_data
        if os.access(base_dir, os.W_OK):
            can_write_local = True

    if can_write_local:
        return local_data_path

    # FALLBACK: Standard AppData/Home location
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, app_name)
    
    return os.path.expanduser(f"~/.{app_name}")

