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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Research Software Group at ISIS (see AUTHORS)

import typing

from icecream import ic
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Qt, QMutex
from qtpy.QtWidgets import QTreeView

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.SubclassViewer import JobTree
from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeItem


class ActionsHolder(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mutex = QMutex()
        self._node_numbers = []
        self._nodes = {}
        self._next_number = 1
        # the nodes used for structuring the data tree
        # will be kept here
        self._sections = {}
        self._section_names = []

    @Slot(object)
    def append_object(self, thing):
        self.mutex.lock()
        self._nodes[self._next_number] = thing
        self._node_numbers.append(self._next_number)
        retval = int(self._next_number)
        self._next_number += 1
        self.mutex.unlock()
        return retval


class ActionsSuperModel(QObject):
    """This object will create and store all the possible
    tree models of actions. These will be assigned to the
    ActionsTree widget, depending on which data object
    has been selected."""

    def __init__(
        self,
        viewer: typing.Optional["QTreeView"] = None,
        parent: typing.Optional["QObject"] = None,
    ) -> None:
        super().__init__(parent)

        self.viewer = viewer
        self.models = {}
        self.currentItem = None
        self.currentModel = None

    def setViewer(self, viewer):
        self.viewer = viewer

    @Slot(DataTreeItem)
    def switchModel(self, item: DataTreeItem):
        """Changes the model behind the viewer to match
        the item selected in the DataView.

        Arguments:
            ancestor -- name of the MDANSE object type
                        selected in the DataView.
        """
        ic("received item:", item)
        ancestor = item.ancestors()[-1]
        try:
            current_model = self.models[ancestor]
        except KeyError:
            current_model = JobTree()
        self.viewer.setModel(current_model)
        self.current_model = current_model
        self.currentItem = item

    def buildModels(self, parent_classes: list):
        """Creates several subtrees out of the registry tree.
        Each tree will only contain nodes that share the same
        ancestor.

        Arguments:
            registry -- an existing RegistryTree instance
            which has been used to scan the MDANSE registry
        """
        for parent_class in parent_classes:
            model = JobTree()
            model.populateTree(parent_class=parent_class)
            self.models[parent_class.__name__] = model
        ic("Build the following models:", self.models.keys())
        self.current_model = self.models["IJob"]

    def copyNodeIntoModel(self, thing: typing.Any, model: ActionsHolder):
        node_parents = thing.category
        rootnode = None
        for name in node_parents:
            if name not in model._section_names:
                section_node = QStandardItem()
                section_node.setText(name)
                if rootnode is None:
                    model.appendRow(section_node)
                else:
                    rootnode.appendRow(section_node)
                model._section_names.append(name)
                model._sections[name] = section_node
                rootnode = section_node
            else:
                rootnode = model._sections[name]
        node_text = thing.label
        node_number = model.append_object(thing)
        ic(node_number)
        newitem = QStandardItem()
        newitem.setText(node_text)
        newitem.setData(node_number)
        if rootnode is None:
            model.appendRow(newitem)
        else:
            rootnode.appendRow(newitem)
