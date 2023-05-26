# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Resources.py
# @brief     Access to external files (icons, etc.)
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from qtpy.QtCore import QDir
from qtpy.QtGui import QIcon



class Resources():

    def __init__(self):
        self._icons = {}
        self.load_icons()
    
    def load_icons(self):
        from importlib.resources import files
        temp = files('MDANSE_GUI.PyQtGUI')
        # print(f"I got {temp} from the importlib.resources")
        res_dir = QDir(str(temp.joinpath('Icons')))
        print(f"Resources are in {res_dir.absolutePath()}")
        # res_dir.addSearchPath('icons', 'Src/PyQtGUI/Icons/')
        res_dir.setNameFilters(["*.png"])
        files = res_dir.entryList()
        for f in files:
            label = ".".join(str(f).split('.')[:-1])
            self._icons[label] = QIcon(res_dir.filePath(f))
            # print(f"Loaded {f} from {res_dir}")

    