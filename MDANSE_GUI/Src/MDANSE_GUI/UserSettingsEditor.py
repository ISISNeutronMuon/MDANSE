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

from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QVBoxLayout,
    QApplication,
    QMenu,
    QLineEdit,
    QTreeView,
)
from qtpy.QtCore import Signal, Slot, Qt, QSortFilterProxyModel, QModelIndex
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE_GUI.Session.LocalSession import LocalSession


class UserSettingsModel(QStandardItemModel):

    file_loaded = Signal(str)

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session is None:
            self._session = LocalSession()
            self._session.load()
        else:
            self._session = session
        self.populate_model()
        self.setHeaderData(0, Qt.Orientation.Horizontal, "Item")
        self.setHeaderData(1, Qt.Orientation.Horizontal, "Value")
        self.setHeaderData(2, Qt.Orientation.Horizontal, "Comment")

        self.dataChanged.connect(self.save_new_value)
        # self.scan_model()

    def populate_model(self):
        comments = [
            "Internal software parameters",
            "Recently used paths to files",
            "Preferred units for plotting",
        ]
        for number, attr in enumerate(["_parameters", "_paths", "_units"]):
            if hasattr(self._session, attr):
                section = getattr(self._session, attr)
                section_item = QStandardItem(attr)
                section_item.setData(attr)
                section_item.setEditable(False)
                self.appendRow([section_item, QStandardItem(comments[number])])
                for key, value in section.items():
                    key_item, value_item = QStandardItem(key), QStandardItem(value)
                    key_item.setData(key)
                    value_item.setData(value)
                    key_item.setEditable(False)
                    section_item.appendRow([key_item, value_item])

    def scan_model(self):
        """This is meant to be used for debugging purposes only"""

        def scan_children(parent_item: QStandardItem):
            for row in range(parent_item.rowCount()):
                for column in range(parent_item.columnCount()):
                    item = parent_item.child(row, column)
                    print(f"row={row}, column={column}, data={item.data()}")
                    if item.hasChildren():
                        scan_children(item)

        scan_children(self.invisibleRootItem())

    @Slot(QModelIndex)
    def save_new_value(self, item_index: QModelIndex):
        item = self.itemFromIndex(item_index)
        row_number = item.row()
        new_value = item.data(role=Qt.ItemDataRole.DisplayRole)
        key = item.parent().child(row_number, 0).data()
        attribute = item.parent().data()
        try:
            group = getattr(self._session, attribute)
            group[key] = new_value
            setattr(self._session, attribute, group)
        except:
            print(f"Could not store {new_value} in session.{attribute}[{key}]")

    @Slot(str)
    def writeout_settings(self, target_filename: str):
        try:
            self._session.save(target_filename)
        except Exception as e:
            print(f"Writeout failed: {e}")


class UserSettingsEditor(QDialog):
    def __init__(self, *args, current_session=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE User Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.filename_widget = QLineEdit(self)
        layout.addWidget(self.filename_widget)
        if current_session is not None:
            if current_session._filename is not None:
                self.filename_widget.setText(str(current_session._filename))

        self.viewer = QTreeView(self)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)

        self.writeout_button = QPushButton("Save settings", self)
        layout.addWidget(self.writeout_button)
        self.writeout_button.clicked.connect(self.save_changes)

        self.data_model = UserSettingsModel(session=current_session)

        self.proxy_model = QSortFilterProxyModel(self)

        self.proxy_model.setSourceModel(self.data_model)
        self.viewer.setModel(self.proxy_model)
        self.viewer.resizeColumnToContents(0)

    @Slot()
    def save_changes(self):
        target_filename = self.filename_widget.text()
        if len(target_filename) > 0:
            self.data_model.writeout_settings(target_filename)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = UserSettingsEditor()
    root.show()
    app.exec()
