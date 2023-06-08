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

import typing

from icecream import ic
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Qt
from qtpy.QtWidgets import QTreeView

from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE_GUI.PyQtGUI.RegistryViewer import RegistryTree


class ActionsHolder(QStandardItemModel):

    def __init__(self, parent = None):
        super().__init__(parent)

        self._node_numbers = []
        self._nodes = {}



class ActionsSuperModel(QObject):
    """This object will create and store all the possible
    tree models of actions. These will be assigned to the
    ActionsTree widget, depending on which data object
    has been selected."""

    def __init__(self, viewer: typing.Optional['QTreeView'],
                       parent: typing.Optional['QObject'] = None) -> None:
        super().__init__(parent)

        self.viewer = viewer
        self.models = {}

    @Slot(str)
    def switchModel(self, ancestor: str):
        """Changes the model behind the viewer to match
        the item selected in the DataView.

        Arguments:
            ancestor -- name of the MDANSE object type
                        selected in the DataView.
        """
        try:
            current_model = self.models[ancestor]
        except KeyError:
            current_model = ActionsHolder(self)
        self.viewer.setModel(current_model)
    
    def buildModels(self, registry: RegistryTree):
        """Creates several subtrees out of the registry tree.
        Each tree will only contain nodes that share the same
        ancestor.

        Arguments:
            registry -- an existing RegistryTree instance
            which has been used to scan the MDANSE registry
        """
        valid_ancestors = registry._by_ancestor.keys()
        for anc in valid_ancestors:
            model = ActionsHolder(self)
            nodes_added = []
            node_numbers = sorted(registry._by_ancestor[anc])
            for nn in node_numbers:
                if nn not in model._node_numbers:
                    temp_item = registry._nodes[nn]
                    self.copyNodeIntoModel(temp_item, model)
            # here the processing ends
            self.models[anc] = model
    
    def copyNodeIntoModel(self, node: QStandardItem, model: ActionsHolder):
        parent = node.parent()
        node_number = node.data()
        node_text = node.text()
        newitem = QStandardItem()
        newitem.setText(node_text)
        newitem.setData(node_number, role = Qt.ItemDataRole.UserRole)
        if parent is not None:
            parent_number = parent.data()
            if parent_number not in model._node_numbers:
                newparent = self.copyNodeIntoModel(parent, model)
            else:
                newparent = model._nodes[parent_number]
            newparent.appendRow(newitem)
        else:
            model.appendRow(newitem)
        model._nodes[node_number] = newitem
        model._node_numbers.append(node_number)
        return newitem
        
