#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import logging
import sys
import os
import time

from qtpy.QtWidgets import QApplication, QSplashScreen, QStyleFactory
from qtpy.QtCore import QSettings, Qt, QTimer
from qtpy.QtGui import QPixmap, QIcon

from MDANSE_GUI.TabbedWindow import TabbedWindow
from MDANSE.MLogging import FMT


os.environ["OMP_NUM_THREADS"] = "1"


def startGUI(some_args):
    logger = logging.getLogger("MDANSE")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel("INFO")
    stream_handler.setFormatter(FMT)
    logger.addHandler(stream_handler)

    app = QApplication(some_args)
    app.setStyle(QStyleFactory.create("Fusion"))

    path = os.path.dirname(os.path.abspath(__file__))
    app.setWindowIcon(QIcon(os.path.join(path, "Icons/MDANSE.ico")))

    settings = QSettings(
        "ISIS Neutron and Muon Source", "MDANSE for Python 3", parent=app
    )

    path = os.path.dirname(os.path.abspath(__file__))
    splash_img = QPixmap(os.path.join(path, "Resources/splash.png"))
    splash = QSplashScreen(splash_img, Qt.WindowStaysOnTopHint)
    splash.show()
    t0 = time.time()
    root = TabbedWindow(
        parent=None, title="MDANSE for Python 3", settings=settings, app_instance=app
    )
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
