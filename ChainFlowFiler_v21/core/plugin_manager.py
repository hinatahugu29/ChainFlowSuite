import os
import sys
import json
import subprocess
from PySide6.QtWidgets import QMessageBox

class PluginManager:
    """
    V19 Plugin Manager
    Handles loading of external tools configuration and launching them.
    """
    def __init__(self, root_dir=None):
        self.tools = []
        self.active_processes = [] # Track running tools
        self.root_dir = root_dir if root_dir else self._detect_root_dir()
        self.config_path = os.path.join(self.root_dir, "tools.json")
        self.load_config()

    def _detect_root_dir(self):
        """Detect root directory (Dev or Frozen)"""
        if getattr(sys, 'frozen', False):
            # Exe: dist/ChainFlowFiler/ChainFlowFiler.exe -> dist/ChainFlowFiler/
            return os.path.dirname(sys.executable)
        else:
            # Dev: G:/CODE/.../ChainFlowFiler_v19/
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_config(self):
        """Load tools.json"""
        if not os.path.exists(self.config_path):
            # Create default config if missing
            self._create_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tools = data.get("tools", [])
        except Exception as e:
            print(f"Error loading tools.json: {e}")

    def _create_default_config(self):
        """Create default configuration with ChainFlowTool"""
        default_tools = {
            "version": "1.0",
            "tools": [
                {
                    "name": "ChainFlow Tool",
                    "id": "chainflow_tool",
                    "description": "Rich content viewer and editor (HTML, PDF, Markdown)",
                    "extensions": [".html", ".htm", ".pdf", ".md"],
                    "executable_path": "../ChainFlowTool/ChainFlowTool.exe", 
                    "script_path": "../ChainFlowTool/editor.py",
                    "arguments": ["--file", "{FILE_PATH}"]
                },
                {
                    "name": "Quick Image Tool",
                    "id": "image_tool",
                    "description": "Image converter and resizer.",
                    "extensions": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"],
                    "executable_path": "../ChainFlowImage/image_tool.exe",
                    "script_path": "../ChainFlowImage/image_tool.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Search",
                    "id": "search_tool",
                    "description": "Fast file search utility.",
                    "extensions": [],
                    "executable_path": "../ChainFlowSearch/ChainFlowSearch.exe",
                    "script_path": "../ChainFlowSearch/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Designer",
                    "id": "designer_tool",
                    "description": "DTP Editor for layout and design.",
                    "extensions": [".cfd", ".pydtp"],
                    "executable_path": "../ChainFlowDesigner/ChainFlowDesigner.exe",
                    "script_path": "../ChainFlowDesigner/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow ToDo",
                    "id": "todo_tool",
                    "description": "Simple ToDo list manager.",
                    "extensions": [],
                    "executable_path": "../ChainFlowToDo/ChainFlowToDo.exe",
                    "script_path": "../ChainFlowToDo/main.py",
                    "arguments": []
                },
                {
                    "name": "ChainFlow PDF Studio",
                    "id": "pdf_studio",
                    "description": "Advanced PDF manipulation tool.",
                    "extensions": [".pdf"],
                    "executable_path": "../ChainFlowPDFStudio/ChainFlowPDFStudio.exe",
                    "script_path": "../ChainFlowPDFStudio/app/main.py",
                    "arguments": []
                },
                {
                    "name": "ChainFlow PDF Compare",
                    "id": "pdf_compare",
                    "description": "Multi-view PDF comparison tool with fractal workspaces.",
                    "extensions": [".pdf"],
                    "executable_path": "../ChainFlowPDFCompare/ChainFlowPDFCompare.exe",
                    "script_path": "../ChainFlowPDFCompare/main.py",
                    "arguments": ["{FILE_PATH}"]
                }
            ]
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_tools, f, indent=4)
        except Exception as e:
            print(f"Error creating default tools.json: {e}")

    def get_tool_for_file(self, file_path):
        """Find the first tool that supports the file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        for tool in self.tools:
            if ext in tool.get("extensions", []):
                return tool
        return None

    def launch_tool(self, tool, file_path, parent_widget=None):
        """Launch the specified tool with the file"""
        cmd = []
        
        # Resolve executable path
        if getattr(sys, 'frozen', False):
            # Frozen: Relate to dist/ChainFlowFiler/
            # Path in config is relative to Filer exe dir (e.g. "../ChainFlowTool/ChainFlowTool.exe")
            # But we should normalize it.
            exe_rel = tool.get("executable_path", "")
            exe_full = os.path.abspath(os.path.join(self.root_dir, exe_rel))
            
            # Simple fallback search if customized path fails but standard suite exists
            if not os.path.exists(exe_full):
                 # Try sibling directory assumption (Suite structure)
                 # dist/ChainFlowTool/ChainFlowTool.exe
                 suite_dir = os.path.dirname(self.root_dir)
                 tool_dir_name = os.path.basename(os.path.dirname(exe_rel.replace("..", ""))) # e.g. ChainFlowTool
                 exe_name = os.path.basename(exe_rel)
                 candidate = os.path.join(suite_dir, tool_dir_name, exe_name)
                 if os.path.exists(candidate):
                     exe_full = candidate

            if not os.path.exists(exe_full):
                if parent_widget:
                    QMessageBox.critical(parent_widget, "Tool Not Found", f"Executable not found:\n{exe_full}")
                return False
            
            cmd = [exe_full]
        else:
            # Dev Mode
            script_rel = tool.get("script_path", "")
            script_full = os.path.abspath(os.path.join(self.root_dir, script_rel))
            
            if not os.path.exists(script_full):
                # Fallback: sibling directory search
                grandparent = os.path.dirname(self.root_dir) # Py_FILE
                tool_folder = os.path.basename(os.path.dirname(script_rel.replace("..", "")))
                script_name = os.path.basename(script_rel)
                candidate = os.path.join(grandparent, tool_folder, script_name)
                if os.path.exists(candidate):
                    script_full = candidate
                elif os.path.exists(os.path.join(grandparent, tool_folder, "app", script_name)):
                    script_full = os.path.join(grandparent, tool_folder, "app", script_name)
            
            if not os.path.exists(script_full):
                if parent_widget:
                    QMessageBox.critical(parent_widget, "Tool Not Found", f"Script not found:\n{script_full}")
                return False
                
            cmd = [sys.executable, script_full]

        # Build arguments
        raw_args = tool.get("arguments", [])
        for arg in raw_args:
            if arg == "{FILE_PATH}":
                cmd.append(file_path)
            # Add other placeholders if needed (e.g. {GEOMETRY})
            elif arg == "{GEOMETRY}" and parent_widget:
                geo = parent_widget.geometry()
                cmd.append(f"--geometry={geo.x()},{geo.y()},{geo.width()},{geo.height()}")
            else:
                cmd.append(arg)
        
        # Launch
        try:
            proc = subprocess.Popen(cmd)
            self.active_processes.append(proc)
            return True
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Launch Error", f"Failed to launch tool:\n{e}")
            return False

    def terminate_all(self):
        """Terminate all launched tool processes"""
        for proc in self.active_processes:
            try:
                if proc.poll() is None: # Running
                    proc.terminate()
                    # Optional: wait a bit and kill if stubborn?
            except Exception:
                pass
        self.active_processes.clear()
