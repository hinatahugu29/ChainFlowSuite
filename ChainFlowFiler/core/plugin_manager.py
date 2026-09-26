import os
import sys
import json
import subprocess
import glob
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
        """Detect root directory (simple location of exe or script)"""
        if getattr(sys, 'frozen', False):
            # Frozen: Root is exactly where the EXE is (e.g., Filer/Internal)
            return os.path.normpath(os.path.dirname(sys.executable))
        else:
            # Dev: Root is exactly where main.py is (e.g., Filer)
            # abspath(__file__) is core/plugin_manager.py -> core -> root
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
        """Create default configuration with the full ChainFlow Suite (Dual-Path Strategy)"""
        default_tools = {
            "version": "1.0",
            "tools": [
                {
                    "name": "ChainFlow Writer",
                    "id": "writer_tool",
                    "description": "Powerful markdown and smart text editor.",
                    "extensions": [".md", ".txt", ".markdown", ".py", ".c", ".cpp", ".h", ".js", ".css", ".json"],
                    "executable_path": "../../ChainFlowWriter/ChainFlowWriter.exe",
                    "script_path": "../ChainFlowWriter/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Tool",
                    "id": "chainflow_tool",
                    "description": "Rich content viewer and editor (HTML, PDF, Markdown)",
                    "extensions": [".html", ".htm", ".pdf", ".md"],
                    "executable_path": "../../ChainFlowTool/ChainFlowTool.exe",
                    "script_path": "../ChainFlowTool/editor.py",
                    "arguments": ["--file", "{FILE_PATH}"]
                },
                {
                    "name": "Quick Image Tool",
                    "id": "image_tool",
                    "description": "Image converter and resizer.",
                    "extensions": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"],
                    "executable_path": "../../ChainFlowImage/image_tool.exe",
                    "script_path": "../ChainFlowImage/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Sniper",
                    "id": "sniper_tool",
                    "description": "Screen capture and OCR tool.",
                    "extensions": [".png", ".jpg"],
                    "executable_path": "../../ChainFlowSniper/ChainFlowSniper.exe",
                    "script_path": "../ChainFlowSniper/main.py",
                    "arguments": []
                },
                {
                    "name": "ChainFlow Pad",
                    "id": "pad_tool",
                    "description": "Lightweight scratchpad and notes.",
                    "extensions": [".txt", ".md"],
                    "executable_path": "../../ChainFlowPad/Internal/ChainFlowPad.exe",
                    "script_path": "../ChainFlowPad/main.py",
                    "arguments": []
                },
                {
                    "name": "Global Search",
                    "id": "search_tool",
                    "description": "Full-text search across the suite.",
                    "extensions": [],
                    "executable_path": "../../ChainFlowSearch/ChainFlowSearch.exe",
                    "script_path": "../ChainFlowSearch/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Designer",
                    "id": "designer_tool",
                    "description": "Workflow and diagram designer.",
                    "extensions": [".flow"],
                    "executable_path": "../../ChainFlowDesigner/ChainFlowDesigner.exe",
                    "script_path": "../ChainFlowDesigner/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow ToDo",
                    "id": "todo_tool",
                    "description": "Task management and todo list.",
                    "extensions": [".todo"],
                    "executable_path": "../../ChainFlowToDo/ChainFlowToDo.exe",
                    "script_path": "../ChainFlowToDo/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow PDF Studio",
                    "id": "pdf_studio",
                    "description": "Advanced PDF editor and annotator.",
                    "extensions": [".pdf"],
                    "executable_path": "../../ChainFlowPDFStudio/ChainFlowPDFStudio.exe",
                    "script_path": "../ChainFlowPDFStudio/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow PDF Compare",
                    "id": "pdf_compare",
                    "description": "Multi-view PDF comparison tool with fractal workspaces.",
                    "extensions": [".pdf"],
                    "executable_path": "../../ChainFlowPDFCompare/ChainFlowPDFCompare.exe",
                    "script_path": "../ChainFlowPDFCompare/main.py",
                    "arguments": ["{FILE_PATH}"]
                },
                {
                    "name": "ChainFlow Zipper",
                    "id": "zipper_tool",
                    "description": "Super fast parallel ZIP compressor",
                    "extensions": [],
                    "executable_path": "../../ChainFlowZipper/target/debug/ChainFlowZipper.exe",
                    "script_path": "",
                    "arguments": []
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
        # Resolve path candidates
        exe_rel = tool.get("executable_path", "")
        script_rel = tool.get("script_path", "")
        
        # Use abspath to resolve relative segments like '..' reliably
        exe_full = os.path.normpath(os.path.abspath(os.path.join(self.root_dir, exe_rel)))
        script_full = os.path.normpath(os.path.abspath(os.path.join(self.root_dir, script_rel)))
        
        # Determine Launch Mode with Fallbacks
        is_frozen = getattr(sys, 'frozen', False)
        target_path = ""
        launch_as_script = False

        if is_frozen:
            # Prefer EXE in frozen mode, but fallback to script if EXE missing
            if os.path.isfile(exe_full):
                target_path = exe_full
            elif os.path.isfile(script_full):
                target_path = script_full
                launch_as_script = True
        else:
            # Prefer script in dev mode, but fallback to EXE if script missing
            if os.path.isfile(script_full):
                target_path = script_full
                launch_as_script = True
            elif os.path.isfile(exe_full):
                target_path = exe_full

        # Final Validation & Launch
        if not target_path or not os.path.isfile(target_path):
            error_msg = f"Tool not found.\n\nChecked paths:\n- EXE: {exe_full}\n- Script: {script_full}"
            if parent_widget:
                QMessageBox.critical(parent_widget, "Tool Not Found", error_msg)
            return False

        if launch_as_script:
            cmd = ["py", target_path]
        else:
            cmd = [target_path]

        # Build arguments
        raw_args = tool.get("arguments", [])
        for arg in raw_args:
            cmd.append(arg.replace("{FILE_PATH}", file_path))
        
        # Launch
        try:
            proc = subprocess.Popen(cmd)
            self.active_processes.append(proc)
            return True
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Launch Error", f"Failed to launch tool:\n{e}")
            return False

    def release_all(self):
        """起動したツールへの参照だけを手放す（プロセスは終了させない）。

        v23.8: Filer の終了時に terminate_all() を呼んでいたため、Writer や
        ToDo など別アプリとして起動したツールが未保存のまま道連れで落ちていた。
        通常終了ではこちらを使い、ツールは独立して生き残らせる。
        """
        self.active_processes.clear()

    def terminate_all(self):
        """Terminate all launched tool processes

        注意: 通常のアプリ終了では呼ばないこと（release_all を使う）。
        起動したツールを明示的に一括終了したい場合のみ使用する。
        """
        for proc in self.active_processes:
            try:
                if proc.poll() is None: # Running
                    proc.terminate()
                    # Optional: wait a bit and kill if stubborn?
            except Exception:
                pass
        self.active_processes.clear()
