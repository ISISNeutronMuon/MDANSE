# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/DataViewModel/TrajectoryHolder.py
# @brief     Subclass of QStandardItemModel for MD trajectories
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import QObject

class TrajectoryHolder(QStandardItemModel):

    def __init__(self, parent: QObject = None):
        super.__init__(self, parent=parent)
