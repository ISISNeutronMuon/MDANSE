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
from __future__ import annotations

from qtpy.QtCore import QObject, QTimer, Signal, Slot
from qtpy.QtGui import QColor, QIcon
from qtpy.QtWidgets import QTabWidget


class NotificationTabWidget(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal_colours = {}
        self._special_color = QColor(250, 10, 50)

    def addTab(self, widget: QObject, name: str) -> int:
        object_id = super().addTab(widget, name)
        self._normal_colours[object_id] = self.tabBar().tabTextColor(object_id)
        widget._tab_reference.set_my_id(object_id)
        widget._tab_reference.notify_user.connect(self.set_special_color)
        return object_id

    @Slot(int)
    def set_special_color(self, tab_index: int):
        if tab_index != self.currentIndex():
            self.tabBar().setTabTextColor(tab_index, self._special_color)
            self.tabBar().setTabIcon(
                tab_index, QIcon.fromTheme(QIcon.ThemeIcon.DialogInformation)
            )

    @Slot(int)
    def reset_current_color(self):
        tab_index = self.tabBar().currentIndex()
        self.tabBar().setTabTextColor(tab_index, self._normal_colours[tab_index])
        self.tabBar().setTabIcon(tab_index, QIcon())

    @Slot(int)
    def reset_color(self, tab_index: int):
        self.tabBar().setTabTextColor(tab_index, self._normal_colours[tab_index])
        self.tabBar().setTabIcon(tab_index, QIcon())
