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

from MDANSE_GUI.PyQtGUI.TabbedWindow import TabbedWindow
from MDANSE_GUI.PyQtGUI.BackEnd import BackEnd


def startGUI(some_args):
    app = QApplication(some_args)
    #
    settings = QSettings(
        "ISIS Neutron and Muon Source", "MDANSE for Python 3", parent=app
    )
    root = TabbedWindow(parent=None, title="MDANSE for Python 3", settings=settings)
    root.show()
    app.exec()  # once this is done, the GUI has its event loop running.
    # no more Python scripting now, we are in the event loop.


if __name__ == "__main__":
    startGUI(sys.argv)
