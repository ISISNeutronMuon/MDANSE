# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Icons/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from PyQt6.QtCore import QDir
from PyQt6.QtGui import QIcon

class PyQtIcons():
            
    def __init__(self, path):

        self.res_dir = QDir(path)
        self._icons = {}
        self.res_dir.setNameFilters(["*.png"])
        files = self.res_dir.entryList()
        for f in files:
            label = ".".join(str(f).split('.')[:-1])
            self._icons[label] = QIcon(self.res_dir.filePath(f))
        
ICONS = PyQtIcons('.')     
