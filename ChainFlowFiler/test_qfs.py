import os, tempfile, sys
from PySide6.QtWidgets import QApplication, QFileSystemModel
from PySide6.QtCore import QTimer
import win32com.client

app = QApplication(sys.argv)
d = tempfile.mkdtemp()
f = os.path.join(d, 'target_folder')
os.mkdir(f)
shell = win32com.client.Dispatch('WScript.Shell')
shortcut = shell.CreateShortcut(os.path.join(d, 'link.lnk'))
shortcut.TargetPath = f
shortcut.Save()

model = QFileSystemModel()
model.setResolveSymlinks(False)  # This is the test!

def check():
    idx = model.index(d)
    if model.rowCount(idx) > 0:
        for i in range(model.rowCount(idx)):
            child = model.index(i, 0, idx)
            print(f"Path: {model.filePath(child)}, Name: {model.fileName(child)}, isDir: {model.isDir(child)}")
        app.quit()

model.directoryLoaded.connect(check)
model.setRootPath(d)
app.exec()
