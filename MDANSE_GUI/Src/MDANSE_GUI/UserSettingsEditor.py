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

from contextlib import suppress

from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal, Slot
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.Session import Session


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
        with suppress(AttributeError):
            model = model.sourceModel()

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
    def __init__(self, *args, current_session: Session | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE User Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self._session = current_session

        self.viewer = SettingsView(self)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)

        if self._session:
            self.data_model = self._session._settings
            self.proxy_model = QSortFilterProxyModel(self)
            self.proxy_model.setSourceModel(self.data_model)
            self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
            self.viewer.setModel(self.proxy_model)
            self.expand_columns()

        self.writeout_button = QPushButton("Save settings", self)
        layout.addWidget(self.writeout_button)
        self.writeout_button.clicked.connect(self.save_changes)
        self.viewer.expanded.connect(self.expand_columns)

    @Slot()
    def expand_columns(self):
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    @Slot()
    def save_changes(self) -> None:
        self._session.save()

    def refresh(self) -> None:
        if not self._session:
            return
        self._session._settings.populate_model()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = UserSettingsEditor()
    root.show()
    app.exec()
