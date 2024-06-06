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
from qtpy.QtCore import Signal, Slot, Qt, QSortFilterProxyModel
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE_GUI.Session.LocalSession import LocalSession


class UserSettingsModel(QStandardItemModel):

    file_loaded = Signal(str)

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session is None:
            self._session = LocalSession()
            self._session.load_json()
        else:
            self._session = session
        self.populate_model()

    def populate_model(self):
        for attr in ["_parameters", "_paths", "_units"]:
            if hasattr(self._session, attr):
                section = getattr(self._session, attr)
                section_item = QStandardItem(attr)
                section_item.setEditable(False)
                self.appendRow([section_item, QStandardItem("")])
                for key, value in section.items():
                    key_item, value_item = QStandardItem(key), QStandardItem(value)
                    key_item.setEditable(False)
                    section_item.appendRow([key_item, value_item])

    @Slot(str)
    def writeout_settings(self, target_filename: str):
        try:
            self._session.save_json(target_filename)
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

        self.viewer = QTreeView(self)
        self.viewer.setHeaderHidden(True)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)

        self.writeout_button = QPushButton("Save settings", self)
        layout.addWidget(self.writeout_button)

        self.data_model = UserSettingsModel(session=current_session)

        self.proxy_model = QSortFilterProxyModel(self)

        self.proxy_model.setSourceModel(self.data_model)
        self.viewer.setModel(self.proxy_model)
        self.viewer.resizeColumnToContents(0)

    def save_changes(self):
        target_filename = self.filename_widget.text()
        self.data_model.writeout_settings(target_filename)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = UserSettingsEditor()
    root.show()
    app.exec()
