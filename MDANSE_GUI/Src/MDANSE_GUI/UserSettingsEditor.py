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

from PyQt6.QtWidgets import QWidget
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
from qtpy.QtGui import QStandardItem, QStandardItemModel, QContextMenuEvent

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

    @Slot()
    def append_group(self):
        self.appendRow(
            [
                QStandardItem("new group, please rename"),
                QStandardItem(),
                QStandardItem("# new section"),
            ]
        )

    @Slot(int)
    def append_child(self, parent_row_number: int):
        parent_item = self.item(parent_row_number, 0)
        parent_item.appendRow(
            [
                QStandardItem("item"),
                QStandardItem("dummy_value"),
                QStandardItem("# new item!"),
            ]
        )

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
        item_key = None
        row_number = item.row()
        new_value = item.data(role=Qt.ItemDataRole.DisplayRole)
        if item.parent() is not None:
            item_key = item.parent().child(row_number, 0).data()
            group_key = item.parent().data()
        else:
            group_key = new_value
        try:
            group = self._settings.group(group_key)
            if item_key is not None:
                group.set(item_key, new_value)
        except:
            print(f"Could not store {new_value} in group[{group_key}]->[{item_key}]")

    @Slot()
    def writeout_settings(self):
        self._settings.save_values()


class SettingsView(QTreeView):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def populateMenu(self, menu: QMenu, clicked_on_node: bool):
        if clicked_on_node:
            for action, method in [("Delete", self.delete_node)]:
                temp_action = menu.addAction(action)
                temp_action.triggered.connect(method)
            menu.addSeparator()
            for action, method in [("Add new entry", self.append_child)]:
                temp_action = menu.addAction(action)
                temp_action.triggered.connect(method)
        for action, method in [("Add new group", self.append_group)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    def inner_model(self):
        model = self.model()
        try:
            model = model.sourceModel()
        except AttributeError:
            pass
        return model

    @Slot()
    def delete_node(self):
        model = self.inner_model()
        index = self.currentIndex()
        model.removeRow(index.row())

    @Slot()
    def append_child(self):
        model = self.inner_model()
        index = self.currentIndex()
        model.append_child(index.row())

    @Slot()
    def append_group(self):
        model = self.inner_model()
        model.append_group()


class UserSettingsEditor(QDialog):
    def __init__(self, *args, current_session=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE User Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.filename_widget = QComboBox(self)
        layout.addWidget(self.filename_widget)
        self._session = current_session

        self.viewer = SettingsView(self)
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
