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


from qtpy.QtCore import QObject, Slot, Signal, QSortFilterProxyModel, QModelIndex
from qtpy.QtWidgets import (
    QDialog,
    QTreeView,
    QGridLayout,
    QLabel,
    QApplication,
    QLineEdit,
    QTextEdit,
)

from MDANSE_GUI.Tabs.Models.JobTree import JobTree

# we check what attributes always exist in a Python object.
# we will not include those in the tree view, since they
# are not defined by the MDANSE code.
to_be_omitted = dir(None)


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
