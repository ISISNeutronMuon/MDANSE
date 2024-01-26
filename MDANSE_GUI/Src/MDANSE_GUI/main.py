# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/main.py
# @brief     Starts the QApplication instance
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

import sys

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QSettings, QThread

from MDANSE_GUI.MainWindow import Main
from MDANSE_GUI.BackEnd import BackEnd


def startGUI(some_args):
    # qdarktheme.enable_hi_dpi()
    app = QApplication(some_args)  # this is quite important, just to activate Qt
    # the settings object should let us save the GUI layout
    # app.setStyleSheet(dark_stylesheet)  # let's change the appearance
    # qdarktheme.setup_theme("auto")  # OS mode
    # qdarktheme.setup_theme("light")  # light mode
    # qdarktheme.setup_theme()  # dark mode
    #
    settings = QSettings(
        "ISIS Neutron and Muon Source", "MDANSE for Python 3", parent=app
    )
    # the backend has no parent, because it runs in a separate QThread
    backend = BackEnd(parent=None, python=sys.executable)
    # backend_thread = QThread()
    # backend.moveToThread(backend_thread)
    # backend_thread.start()
    # Main is the main window of the GUI
    # It runs in the main thread, and has to connect to the BackEnd
    # using slots and signals.
    root = Main(parent=None, title="MDANSE for Python 3", settings=settings)
    # root.destroyed.connect(backend_thread.exit)
    root.setBackend(backend)
    root.show()
    app.exec()  # once this is done, the GUI has its event loop running.
    # no more Python scripting now, we are in the event loop.


if __name__ == "__main__":
    startGUI(sys.argv)