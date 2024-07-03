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
    QComboBox,
    QTreeView,
)
from qtpy.QtCore import Signal, Slot, Qt, QSortFilterProxyModel, QModelIndex
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE_GUI.Session.StructuredSession import (
    StructuredSession,
    SettingsFile,
    SettingsGroup,
)


class UserSettingsModel(QStandardItemModel):

    file_loaded = Signal(str)

    def __init__(self, *args, settings_filename: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        if settings_filename:
            self._settings = SettingsFile(settings_filename)
            self._settings.load_from_file()
        else:
            return
        self.populate_model()
        self.setHeaderData(0, Qt.Orientation.Horizontal, "Item")
        self.setHeaderData(1, Qt.Orientation.Horizontal, "Value")
        self.setHeaderData(2, Qt.Orientation.Horizontal, "Comment")

        self.dataChanged.connect(self.save_new_value)
        # self.scan_model()

    def populate_model(self):
        for number, groupname in enumerate(self._settings.keys()):
            group = self._settings.group(groupname)
            section = group._name
            section_item = QStandardItem(section)
            section_item.setData(section)
            section_item.setEditable(False)
            section_comment = group._group_comment
            self.appendRow(
                [section_item, QStandardItem(), QStandardItem(section_comment)]
            )
            for key, value in group.as_dict().items():
                key_item, value_item = QStandardItem(key), QStandardItem(value)
                key_item.setData(key)
                value_item.setData(value)
                comment_item = QStandardItem(group._comments[key])
                comment_item.setData(group._comments[key])
                key_item.setEditable(False)
                section_item.appendRow([key_item, value_item, comment_item])

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

    @Slot()
    def writeout_settings(self):
        self._settings.save_values()


class UserSettingsEditor(QDialog):
    def __init__(self, *args, current_session=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE User Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.filename_widget = QComboBox(self)
        layout.addWidget(self.filename_widget)
        self._session = current_session

        self.viewer = QTreeView(self)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)

        self.writeout_button = QPushButton("Save settings", self)
        layout.addWidget(self.writeout_button)
        self.writeout_button.clicked.connect(self.save_changes)
        self.filename_widget.currentTextChanged.connect(self.switch_model)
        self.viewer.expanded.connect(self.expand_columns)

    @Slot(str)
    def switch_model(self, model_key: str):
        self.data_model = UserSettingsModel(settings_filename=model_key)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.data_model)
        self.viewer.setModel(self.proxy_model)
        self.expand_columns()

    @Slot()
    def expand_columns(self):
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    def update_combo(self):
        self.filename_widget.clear()
        if self._session is not None:
            self.filename_widget.addItems(
                [str(x) for x in self._session._configs.keys()]
            )
            self.filename_widget.setCurrentText(self._session._main_config_name)

    @Slot()
    def save_changes(self):
        self.data_model.writeout_settings()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = UserSettingsEditor()
    root.show()
    app.exec()
