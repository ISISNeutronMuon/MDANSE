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

import hashlib

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot

from MDANSE.Framework.InputData import InputFileData

class TrajectoryItem(QStandardItem):

    def __init__(self, *args, trajectory = None):
        super().__init__(*args)
        self._trajectory = trajectory


class TrajectoryHolder(QStandardItemModel):

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)

    @Slot(object)
    def addItem(self, new_entry: InputFileData):
        traj = TrajectoryItem(new_entry.basename, trajectory = new_entry)
        self.appendRow([traj])


class FileObject():

    def __init__(self, hash_function = hashlib.sha256):

        self.filename = ""
        self.absolute_path = ""
        self.relative_path = '.'
        self.hash_function = hash_function


class DataTreeItem(QStandardItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.mdanse_tag = kwargs['mdanse_tag']
        except KeyError:
            self.mdanse_tag = 'unknown'
        
        self.original_input = []
        self.processing_used = ""
        self.processing_parameters = {}

    def showHistory(self):
        history = ";".join(self.ancestors())
        return history
    
    def ancestors(self):
        parent = self.parent()
        if parent is None:
            return [self.mdanse_tag]
        else:
            return parent.ancestors() + [self.mdanse_tag]


class TrajectoryItem(DataTreeItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.original_input = []
        self.processing_used = ""
        self.processing_parameters = {}


class AnalysisItem(DataTreeItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class DataTreeModel(QStandardItemModel):

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)

    @Slot(object)
    def addItem(self, new_entry: InputFileData):
        traj = TrajectoryItem(new_entry.basename, trajectory = new_entry)
        self.appendRow([traj])
