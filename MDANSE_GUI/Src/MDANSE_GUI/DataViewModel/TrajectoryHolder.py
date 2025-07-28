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
from __future__ import annotations

import hashlib
import os
from pathlib import PurePath

from qtpy.QtCore import QObject, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class FileObject:
    def __init__(self, hash_function=hashlib.sha256):
        self.filename = ""
        self.absolute_path = ""
        self.extension = ".*"
        self.relative_path = "."
        self.hash_function = hash_function
        self.hash = -1

    def setFilename(self, some_fname: str):
        fname = str(some_fname)
        abspath, filename = os.path.split(fname)
        self.extension = str(filename).split(".")[-1]
        self.filename = filename
        self.absolute_path = PurePath(abspath)
        self.hash = self.calculateHash(fname)

    def calculateHash(self, fname, chunk_size=1024 * 512):
        hash_object = self.hash_function()
        with open(fname, "br") as source:
            while chunk := source.read(chunk_size):
                hash_object.update(chunk)
        return hash_object.hexdigest()


class DataTreeItem(QStandardItem):
    def __init__(self, *args, **kwargs):
        new_kwargs = {}
        for key, val in kwargs.items():
            if key not in ["mdanse_tag"]:
                new_kwargs[key] = val
        super().__init__(*args, **new_kwargs)

        self.mdanse_tag = kwargs.get("mdanse_tag", "unknown")

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
        new_kwargs = {}
        for key, val in kwargs.items():
            if key not in ["fname", "trajectory"]:
                new_kwargs[key] = val
        super().__init__(*args, **new_kwargs)

        self.filename = kwargs.get("fname", "NULL")
        self.trajectory = kwargs.get("trajectory", None)
        self.original_input = []
        self.processing_used = ""
        self.processing_parameters = {}
        self.file_info = FileObject()

        if self.filename != "NULL":
            self.file_info.setFilename(PurePath(self.filename))
        self.setText(os.path.split(self.filename)[1])


class AnalysisItem(DataTreeItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataTreeModel(QStandardItemModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self._trajectory_objects = {}

    @Slot(object)
    def addItem(self, new_entry: Trajectory):
        traj = TrajectoryItem(
            os.path.split(new_entry.filename)[1], trajectory=new_entry
        )
        self.appendRow([traj])
