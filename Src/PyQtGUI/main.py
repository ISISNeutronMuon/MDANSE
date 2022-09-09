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

from PyQt6.QtWidgets import QApplication

from MDANSE.PyQtGUI.MainWindow import Main

def startGUI(some_args):
    app = QApplication(some_args) # this is quite important, just to activate Qt
    root = Main()
    root.show()
    app.exec() # once this is done, the GUI has its event loop running.
    # no more Python scripting now, we are in the event loop.

if __name__ == '__main__':
    startGUI(sys.argv)
