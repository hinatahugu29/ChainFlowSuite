
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import QIODevice, QTextStream

# Add parent directory to path for potential shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_window import SearchWindow

SERVER_NAME = "ChainFlowSearch_Instance"

def main():
    # Windows Taskbar Icon Fix (v21.1)
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.Search.v21")
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # 1. Parse Args (Target Directory)
    start_dir = None
    if len(sys.argv) > 1:
        possible_dir = sys.argv[1]
        # Remove quotes if Windows adds them
        possible_dir = possible_dir.strip('"') 
        if os.path.exists(possible_dir) and os.path.isdir(possible_dir):
            start_dir = os.path.abspath(possible_dir)
        
    # 2. Try Connect to Existing Instance
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    
    if socket.waitForConnected(500):
        # >>> Existing Instance Found >>>
        if start_dir:
            # Send the path to the existing instance
            try:
                # Use encode to send bytes
                socket.write(start_dir.encode('utf-8'))
                socket.waitForBytesWritten(1000)
            except Exception as e:
                print(f"Failed to send arguments: {e}")
        else:
            # Just wake up the window (send empty string)
            socket.write(b"__WAKEUP__")
            socket.waitForBytesWritten(1000)
            
        socket.disconnectFromServer()
        sys.exit(0)
    
    # 3. >>> New Instance (Server) >>>
    server = QLocalServer()
    # Cleanup potential stale server file
    QLocalServer.removeServer(SERVER_NAME)
    
    if not server.listen(SERVER_NAME):
        print(f"Warning: Failed to start local server: {server.errorString()}")
    
    window = SearchWindow(start_dir)
    
    # 4. Handle Incoming Connections (New Tabs)
    def handle_new_connection():
        client_socket = server.nextPendingConnection()
        if client_socket.waitForReadyRead(1000):
            data = client_socket.readAll().data().decode('utf-8').strip()
            
            # Activate Window First
            window.show()
            window.raise_()
            window.activateWindow()
            
            if data and data != "__WAKEUP__":
                 if os.path.exists(data) and os.path.isdir(data):
                     window.add_new_tab(data)
                     
        client_socket.disconnectFromServer()

    server.newConnection.connect(handle_new_connection)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
