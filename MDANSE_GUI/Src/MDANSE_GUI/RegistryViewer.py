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


"""This module contains a RegistryTree data model,
and a RegistryViewer dialog.
The puprose of those is to create a visualisation
of the classes that can be accessed from the
MDANSE IJob interface. 
"""

import os

from MDANSE.Framework.Jobs.IJob import IJob

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import Slot, Signal, QSortFilterProxyModel, QModelIndex
from qtpy.QtWidgets import (
    QDialog,
    QTreeView,
    QGridLayout,
    QLabel,
    QApplication,
    QLineEdit,
    QTextEdit,
)
from qtpy.QtCore import Qt

# we check what attributes always exist in a Python object.
# we will not include those in the tree view, since they
# are not defined by the MDANSE code.
to_be_omitted = dir(None)


class RegistryTree(QStandardItemModel):
    """RegistryTree creates a tree structure
    of QStandardItem objects, and stores information
    about the names and docstrings of different
    classes contained in the IJob object.

    It inherits the QStandardItemModel, so it can be
    used in the Qt data/view/proxy model.
    """

    doc_string = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._nodes = {}  # dict of {number: QStandardItem}
        self._docstrings = {}  # dict of {number: str}
        self._values = {}  # dict of {number: str}

        self._converters = {}
        self._jobs = {}

        self._by_ancestor = {}  # dict of list[int]

        self.nodecounter = 0  # each node is given a unique number
        # the number is the key to the dictionary entries.

        self.populateTree()
        # Some useful debugging here, for now
        # print("Converters")
        # print(self._converters)
        # print("Jobs")
        # print(self._jobs)

    def populateTree(self):
        """This function starts the recursive process of scanning
        the registry tree. Only called once on startup.
        """
        full_dict = IJob.indirect_subclass_dictionary()
        for key in full_dict.keys():
            self.parseNode(full_dict, key)

    def addNode(self, thing, name="Registry", parent: int = -1):
        """This function adds a new node to the tree data model.

        Arguments:
            thing -- a Python class from MDANSE.Framework

        Keyword Arguments:
            name -- the text tag that will be shown in the tree view
                    (default: {"Registry"})
            parent -- number (key) of the parent node in the data model
                    (default: {-1})

        Returns:
            the number of the new node
        """
        item = QStandardItem(name)
        retval = int(self.nodecounter)
        item.setData(retval, role=Qt.ItemDataRole.UserRole)
        self._nodes[self.nodecounter] = item
        self._docstrings[self.nodecounter] = thing.__doc__
        self.nodecounter += 1
        if parent < 0:
            self.appendRow(item)
        else:
            parent_node = self._nodes[parent]
            parent_node.appendRow(item)
        # here start the finer separation into categories
        if hasattr(thing, "ancestor") and hasattr(thing, "section"):
            try:
                cat = thing.category
            except AttributeError:
                pass
            else:
                if len(thing.ancestor) > 0:
                    for ancestor in thing.ancestor:
                        if ancestor not in self._by_ancestor.keys():
                            self._by_ancestor[ancestor] = []
                        self._by_ancestor[ancestor].append(retval)
                try:
                    is_conv = cat[0] == "Converters"
                except IndexError:
                    pass
                else:
                    if is_conv:
                        self._converters[name] = thing.__name__
                    else:
                        self._jobs[name] = thing.__name__
        # end of the finer assignment
        return retval

    def addTerminalNodes(self, thing, parent: int = -1):
        """A separate function for adding nodes to the
        tree structure which are _attributes_ and not
        _classes_.

        Arguments:
            thing -- the attribute of the parent node
            class to be stored here.

        Keyword Arguments:
            parent -- the number of the parent node (default: {-1})
        """
        for attr in dir(thing):
            if attr not in to_be_omitted:
                item = QStandardItem(str(attr))
                attr_object = getattr(thing, attr, None)
                item.setData(self.nodecounter, role=Qt.ItemDataRole.UserRole)
                # self._items.append(item)
                self._nodes[self.nodecounter] = item
                self._docstrings[self.nodecounter] = attr_object.__doc__
                self._values[self.nodecounter] = str(attr_object)
                self.nodecounter += 1
                if parent < 0:
                    self.appendRow(item)
                else:
                    parent_node = self._nodes[parent]
                    parent_node.appendRow(item)

    def parseNode(self, node, name="unknown", parent=-1):
        """A recursive function which discovers information
        about the Python object to be added to the data tree,
        and decides where to add it.

        Arguments:
            node -- the Python object to be added to the data
                   tree

        Keyword Arguments:
            name -- the name tag to be used for the new node
                   (default: {"unknown"})
            parent -- the number of the parent of the new node
                   (default: {-1})
        """
        parent_number = self.addNode(node, name, parent)
        if hasattr(node, "keys"):
            try:
                node.keys()
            except TypeError:
                self.addTerminalNodes(node, parent_number)
            else:
                for key in node.keys():
                    child = node[key]
                    self.parseNode(child, name=str(key), parent=parent_number)
        else:
            self.addTerminalNodes(node, parent_number)

    def getAncestry(self, number: int):
        """This function discovers the keys needed to be put
        into the REGISTRY to get the class attached to the
        specific node.

        Arguments:
            number -- number of the object in the data model.

        Returns:
            list[str] of all the parents of the given node.
        """
        parents = []
        item = self._nodes[number]
        while item is not None:
            parents.append(item.text())
            item = item.parent()
        return parents[::-1]


class RegistryViewer(QDialog):
    """A widget displaying the contents of the MDANSE
    REGISTRY.
    Normally intended to be used as a standalone
    program, since it is of little interest to the
    end users of MDANSE.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Registry Viewer")

        self.glayout = QGridLayout(self)
        self.setLayout(self.glayout)

        self.viewer = QTreeView(self)
        self.viewer.setObjectName("MDANSE Registry")
        self.glayout.addWidget(self.viewer, 0, 0, 4, 2)

        self.glayout.addWidget(QLabel("Filter", self), 4, 0)

        self.filter_field = QLineEdit(self)
        self.glayout.addWidget(self.filter_field, 4, 1)

        self.path_field = QLineEdit(self)
        self.glayout.addWidget(self.path_field, 0, 2)

        self.proxy = QSortFilterProxyModel(self)

        self.datamodel = RegistryTree(self)
        self.proxy.setSourceModel(self.datamodel)

        self.viewer.setModel(self.proxy)

        self.value_panel = QTextEdit(self)
        self.glayout.addWidget(self.value_panel, 1, 2, 2, 1)

        self.doc_panel = QTextEdit(self)
        self.glayout.addWidget(self.doc_panel, 3, 2, 1, 1)

        self.setStyleSheet(
            "QLabel {background-color:rgb(250,250,250); qproperty-alignment: AlignCenter}"
        )
        self.filter_field.textChanged.connect(self.filterEntries)

        self.viewer.clicked.connect(self.updateDocstring)
        self.viewer.clicked.connect(self.updatePath)

    @Slot()
    def filterEntries(self):
        phrase = self.filter_field.text()
        self.proxy.setFilterFixedString(phrase)

    @Slot(QModelIndex)
    def updateDocstring(self, index=QModelIndex):
        n_index = self.viewer.currentIndex()
        number = self.proxy.itemData(n_index)[256]
        try:
            docstring = self.datamodel._docstrings[number]
        except AttributeError:
            docstring = ""
        self.doc_panel.setText(docstring)
        try:
            valstring = self.datamodel._values[number]
        except KeyError:
            valstring = ""
        self.value_panel.setText(valstring)

    @Slot(QModelIndex)
    def updatePath(self, index=QModelIndex):
        n_index = self.viewer.currentIndex()
        number = self.proxy.itemData(n_index)[256]
        parents = self.datamodel.getAncestry(number)
        try:
            valstring = self.datamodel._values[number]
        except KeyError:
            pathstring = "REGISTRY['" + "']['".join(parents) + "']"
        else:
            pathstring = "REGISTRY['" + "']['".join(parents[:-1]) + "']." + parents[-1]
        self.path_field.setText(pathstring)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = RegistryViewer()
    root.show()
    app.exec()
