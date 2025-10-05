import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

# ---------------------------------------------------------------------------
# Compatibility for both PySide2 and PySide6
# ---------------------------------------------------------------------------
try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtCore

import mbb_server

# Keep global reference alive
_window_instance = None

# ---------------------------------------------------------------------------
# Return Maya main window as a QtWidgets.QMainWindow instance.
# ---------------------------------------------------------------------------
def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QMainWindow)

# ---------------------------------------------------------------------------
# Main UI class
# ---------------------------------------------------------------------------
class MBBUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MBBUI, self).__init__(parent)
        self.setWindowTitle("Maya Blender Bridge")
        self.setMinimumWidth(220)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)

        layout = QtWidgets.QVBoxLayout(self)
        self.start_btn = QtWidgets.QPushButton("Start Server")
        self.stop_btn = QtWidgets.QPushButton("Stop Server")
        self.status_label = QtWidgets.QLabel("Status: Stopped")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.status_label)

        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)

        # Check current status.
        if mbb_server._running:
            self.status_label.setText("Status: Running")
            self.start_btn.hide()
            self.stop_btn.show() 
        else:
            self.status_label.setText("Status: Stopped")
            self.start_btn.show()
            self.stop_btn.hide()

    def start_server(self):
        mbb_server.start_server()
        self.status_label.setText("Status: Running")
        self.start_btn.hide()
        self.stop_btn.show() 

    def stop_server(self):
        mbb_server.stop_server()
        self.status_label.setText("Status: Stopped")
        self.start_btn.show()
        self.stop_btn.hide()

# ---------------------------------------------------------------------------
# Function to show the UI in case we closed it.
# ---------------------------------------------------------------------------
def show():
    global _window_instance

    try:
        if _window_instance:
            _window_instance.close()
            _window_instance.deleteLater()
    except:
        pass

    parent = get_maya_window()
    _window_instance = MBBUI(parent)
    _window_instance.show()
    _window_instance.raise_()
    _window_instance.activateWindow()
    print("[MBB UI] Window shown")
    return _window_instance
