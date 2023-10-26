import sys
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QSettings
from MDANSE_GUI.PyQtGUI.MainWindow import Main
from MDANSE_GUI.PyQtGUI.BackEnd import BackEnd

 

def start_gui(some_args):
    app = QApplication(some_args)
    settings = QSettings("ISIS Neutron and Muon Source", "MDANSE for Python 3", parent=app)
    backend = BackEnd(parent=None, python=sys.executable)
    root = Main(parent=None, title="MDANSE for Python 3", settings=settings)
    root.setBackend(backend)
    root.show()
    sys.exit(app.exec_())

 

if __name__ == "__main__":
    start_gui(sys.argv)