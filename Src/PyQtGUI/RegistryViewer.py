
import os

from MDANSE import PLATFORM, REGISTRY

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QSortFilterProxyModel, QModelIndex
from qtpy.QtWidgets import QDialog, QTreeView, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTextEdit
from qtpy.QtCore import Qt

to_be_omitted = dir(None)

class RegistryTree(QStandardItemModel):

    doc_string = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._nodes = {}
        self._docstrings = {}
        # self._items = []  # to avoid garbage collection
        self.nodecounter = 0

        self.populateTree()

    def populateTree(self):
        for key in REGISTRY.interfaces:
            self.parseNode(REGISTRY[key], key)

    def addNode(self, thing, name = "Registry", parent : int = -1):
        item = QStandardItem(name)
        retval = int(self.nodecounter)
        item.setData(retval, role = Qt.ItemDataRole.UserRole)
        self._nodes[self.nodecounter] = item
        self._docstrings[self.nodecounter] = thing.__doc__
        self.nodecounter += 1
        if parent < 0:
            self.appendRow(item)
        else:
            parent_node = self._nodes[parent]
            parent_node.appendRow(item)
        # self._items.append(item)
        return retval

    def addTerminalNodes(self, thing, parent : int = -1):
        for attr in dir(thing):
            if attr not in to_be_omitted:
                item = QStandardItem(str(attr))
                attr_object = getattr(thing,attr,None)
                item.setData(self.nodecounter, role = Qt.ItemDataRole.UserRole)
                # self._items.append(item)
                self._nodes[self.nodecounter] = item
                self._docstrings[self.nodecounter] = attr_object.__doc__
                self.nodecounter += 1
                if parent < 0:
                    self.appendRow(item)
                else:
                    parent_node = self._nodes[parent]
                    parent_node.appendRow(item)

    def parseNode(self, node, name= "unknown", parent = -1):
        parent_number = self.addNode(node, name, parent)
        if hasattr(node, "keys"):
            try:
                node.keys()
            except TypeError:
                self.addTerminalNodes(node, parent_number)
            else:
                for key in node.keys():
                    child = node[key]
                    self.parseNode(child, name = str(key), parent = parent_number)
        else:
            self.addTerminalNodes(node, parent_number)


class RegistryViewer(QDialog):
    """A widget displaying the periodic table of elements.
    Can be used within MDANSE, or as a standalone program.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Registry Viewer")

        self.glayout = QGridLayout(self)
        self.setLayout(self.glayout)

        self.viewer = QTreeView(self)
        self.viewer.setObjectName("MDANSE Registry")
        self.glayout.addWidget(self.viewer,0,0, 1,2)

        self.glayout.addWidget(QLabel("Filter", self),1,0)

        self.filter_field = QLineEdit(self)
        self.glayout.addWidget(self.filter_field, 1,1)

        self.proxy = QSortFilterProxyModel(self)

        self.datamodel = RegistryTree(self)
        self.proxy.setSourceModel(self.datamodel)

        self.viewer.setModel(self.proxy)

        self.side_panel = QTextEdit(self)
        self.glayout.addWidget(self.side_panel, 0,2,1,1)

        self.setStyleSheet("QLabel {background-color:rgb(250,250,250); qproperty-alignment: AlignCenter}")
        self.filter_field.textChanged.connect(self.filterEntries)

        self.viewer.clicked.connect(self.updateDocstring)
    
    @Slot()
    def filterEntries(self):
        phrase = self.filter_field.text()
        self.proxy.setFilterFixedString(phrase)
    
    @Slot(QModelIndex)
    def updateDocstring(self, index = QModelIndex):
        n_index = self.viewer.currentIndex()
        number = self.proxy.itemData(n_index)[256]
        try:
            docstring = self.datamodel._docstrings[number]
        except AttributeError:
            docstring = ""
        self.side_panel.setText(docstring)
    

            
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    root = RegistryViewer()
    root.show()
    app.exec()
