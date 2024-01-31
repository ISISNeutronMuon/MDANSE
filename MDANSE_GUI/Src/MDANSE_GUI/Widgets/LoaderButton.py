# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/MainWindow.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************


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
