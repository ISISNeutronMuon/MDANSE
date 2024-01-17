# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/RegistryViewer.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QPushButton, QTextEdit, QWidget, QTableView

from MDANSE_GUI.PyQtGUI.Widgets.DoublePanel import DoublePanel
from MDANSE_GUI.PyQtGUI.DataViewModel import GeneralModel


class TrajectoryTab(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        trajectory_holder = GeneralModel(self)
        trajectory_list = QTableView(self)
        visualiser = QTextEdit
        core = DoublePanel(self, data_side=trajectory_list, visualiser_side=visualiser)
        core.set_model(trajectory_holder)
