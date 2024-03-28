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


from icecream import ic
from qtpy.QtCore import (
    QPoint,
    Signal,
)
from qtpy.QtWidgets import (
    QToolButton,
    QMenu,
)


class LoaderButton(QToolButton):
    """Subclassed from QToolButton, this object shows the name of a
    chemical element, and creates a pop-up menu giving access to information
    about isotopes when clicked.
    """

    load_hdf = Signal()
    start_converter = Signal(str)

    def __init__(self, *args, caption="Load", backend=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setText(caption)
        # self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.converter_source = backend

        self.clicked.connect(self.altContextMenu)

    # def enterEvent(self, a0: QEnterEvent) -> None:
    #     self.atom_info.emit(self.info)
    #     return super().enterEvent(a0)

    def populateMenu(self, menu: QMenu):
        hdf_action = menu.addAction("Load HDF5")
        hdf_action.triggered.connect(self.load_hdf)
        menu.addSeparator()
        for cjob in self.converter_source.backend.getConverters():
            menu.addAction("Convert using " + str(cjob))

    def altContextMenu(self):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(self.mapToGlobal(QPoint(10, 10)))
        if res is not None and not "HDF5" in res.text():
            self.start_converter.emit(res.text())

    def contextMenuEvent(self, event):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(event.globalPos())
        if res is not None and not "HDF5" in res.text():
            self.start_converter.emit(res.text())
