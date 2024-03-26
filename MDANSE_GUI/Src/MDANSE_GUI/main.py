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
import os
import time

from qtpy.QtWidgets import QApplication, QSplashScreen, QStyleFactory
from qtpy.QtCore import QSettings, Qt, QTimer
from qtpy.QtGui import QPixmap, QIcon

from MDANSE_GUI.TabbedWindow import TabbedWindow


def startGUI(some_args):
    app = QApplication(some_args)
    app.setStyle(QStyleFactory.create("Fusion"))

    path = os.path.dirname(os.path.abspath(__file__))
    app.setWindowIcon(QIcon(os.path.join(path, "MDANSE.ico")))

    settings = QSettings(
        "ISIS Neutron and Muon Source", "MDANSE for Python 3", parent=app
    )

    path = os.path.dirname(os.path.abspath(__file__))
    splash_img = QPixmap(os.path.join(path, "splash.png"))
    splash = QSplashScreen(splash_img, Qt.WindowStaysOnTopHint)
    splash.show()
    t0 = time.time()
    root = TabbedWindow(parent=None, title="MDANSE for Python 3", settings=settings)
    root.show()
    t1 = time.time()
    # only allow the splash screen to stay up for maximum of 2s if the
    # GUI loads fast but closes immediately if GUI was slow to load
    QTimer.singleShot(
        max([0, round(2000 - 1000 * (t1 - t0))]), lambda: splash.finish(root)
    )

    app.exec()  # once this is done, the GUI has its event loop running.
    # no more Python scripting now, we are in the event loop.


if __name__ == "__main__":
    startGUI(sys.argv)
