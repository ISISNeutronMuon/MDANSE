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
import os

from icecream import ic
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot

from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE.Framework.InputData import InputFileData

# class TrajectoryItem(QStandardItem):

#     def __init__(self, *args, trajectory = None):
#         super().__init__(*args)
#         self._trajectory = trajectory


# class TrajectoryHolder(QStandardItemModel):

#     def __init__(self, parent: QObject = None):
#         super().__init__(parent=parent)

#     @Slot(object)
#     def addItem(self, new_entry: InputFileData):
#         traj = TrajectoryItem(new_entry.basename, trajectory = new_entry)
#         self.appendRow([traj])
    
#     @Slot(object)
#     def acceptNewTrajectory(self, new_trajectory):
        
#         data = REGISTRY["input_data"]["hdf_trajectory"](new_trajectory)


class FileObject():

    def __init__(self, hash_function = hashlib.sha256):

        self.filename = ""
        self.absolute_path = ""
        self.extension = ".*"
        self.relative_path = '.'
        self.hash_function = hash_function
        self.hash = -1
    
    def setFilename(self, fname: str):
        abspath, filename = os.path.split(fname)
        self.extension = str(filename).split('.')[-1]
        self.filename = filename
        self.absolute_path = abspath
        self.hash = self.calculateHash(fname)

    def calculateHash(self, fname, chunk_size = 1024*512):
        hash_object = self.hash_function()
        with open(fname,'br') as source:
            while chunk := source.read(chunk_size):
                hash_object.update(chunk)
        return hash_object.hexdigest()


class DataTreeItem(QStandardItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mdanse_tag = kwargs.get('mdanse_tag', 'unknown')
        
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
        
        self.filename = kwargs.get('fname', 'NULL')
        self.trajectory = kwargs.get('trajectory', None)
        self.original_input = []
        self.processing_used = ""
        self.processing_parameters = {}
        self.file_info = FileObject()
        
        if self.filename != 'NULL':
            self.file_info.setFilename(self.filename)
        self.setText(self.filename)


class AnalysisItem(DataTreeItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class DataTreeModel(QStandardItemModel):

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._trajectory_objects = {}

    @Slot(object)
    def addItem(self, new_entry: InputFileData):
        traj = TrajectoryItem(new_entry.basename, trajectory = new_entry)
        self.appendRow([traj])
    
    @Slot(str)
    def acceptNewTrajectory(self, fname: str):
        ic(f"Received {fname}")
        data = REGISTRY["input_data"]["hdf_trajectory"](fname)
        # data = REGISTRY["hdf_trajectory"](fname)
        ic()
        item = TrajectoryItem(filename= fname, data= data, mdanse_tag = "trajectory")
        ic("Created TrajectoryItem")
        self.appendRow(item)
        tkey = item.file_info.hash
        self._trajectory_objects[tkey] = data
        ic("assigned new trajectory to the dictionary")
