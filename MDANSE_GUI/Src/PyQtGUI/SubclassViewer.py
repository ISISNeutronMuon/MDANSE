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


"""This module contains a RegistryTree data model,
and a RegistryViewer dialog.
The puprose of those is to create a visualisation
of the classes that can be accessed from the
MDANSE IJob interface. 
"""

from MDANSE.Framework.Jobs.IJob import IJob

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QSortFilterProxyModel, QModelIndex
from qtpy.QtWidgets import (
    QDialog,
    QTreeView,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QApplication,
    QSizePolicy,
    QMenu,
    QLineEdit,
    QTextEdit,
)
from qtpy.QtCore import Qt

# we check what attributes always exist in a Python object.
# we will not include those in the tree view, since they
# are not defined by the MDANSE code.
to_be_omitted = dir(None)


class JobTree(QStandardItemModel):
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

        self._categories = {}
        self._jobs = {}

        self._by_ancestor = {}  # dict of list[int]

        self.nodecounter = 0  # each node is given a unique number

        self.populateTree()

    def populateTree(self, parent_class=None):
        """This function starts the recursive process of scanning
        the registry tree. Only called once on startup.
        """
        if parent_class is None:
            parent_class = IJob
        full_dict = parent_class.indirect_subclass_dictionary()
        for class_name, class_object in full_dict.items():
            self.createNode(class_name, class_object)

    def createNode(self, name: str, thing):
        """Creates a new QStandardItem. It will store
        the node number as user data. The 'thing' passed to this method
        will be stored by the model in an internal dictionary, where
        the node number is the key

        Arguments:
            name -- the name of the new node
            thing -- any Python object to be stored and attached to the node
        """
        new_node = QStandardItem(name)
        new_number = self.nodecounter + 1
        self.nodecounter += 1
        new_node.setData(new_number, role=Qt.ItemDataRole.UserRole)
        self._nodes[new_number] = new_node
        self._values[new_number] = thing
        self._docstrings[new_number] = thing.__doc__
        if hasattr(thing, "category"):
            parent = self.parentsFromCategories(thing.category)
        else:
            parent = self.invisibleRootItem()
        parent.appendRow(new_node)

    def parentsFromCategories(self, category_tuple):
        """Returns the parent node for a node that belongs to the
        category specified by categore_tuple. Also makes sure that
        the parent nodes exist (or creates them if they don't).

        Arguments:
            category_tuple -- category names (str) in the sequence in which
                they should be placed in the tree structure.

        Returns:
            QStandardItem - the node of the last item in 'category_tuple'
        """
        parent = self.invisibleRootItem()
        for cat_string in category_tuple:
            if not cat_string in self._categories.keys():
                current_node = QStandardItem(cat_string)
                parent.appendRow(current_node)
                parent = current_node
                self._categories[cat_string] = current_node
            else:
                current_node = self._categories[cat_string]
        return current_node


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
