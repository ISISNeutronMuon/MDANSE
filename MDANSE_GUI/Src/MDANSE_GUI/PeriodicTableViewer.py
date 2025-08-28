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

from qtpy.QtCore import QPoint, Qt, Signal, Slot
from qtpy.QtGui import QEnterEvent
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.IO.AtomInfo import atom_info

# from MDANSE.GUI.ElementsDatabaseEditor import ElementsDatabaseEditor

_LAYOUT = {}
_LAYOUT["H"] = (0, 1)
_LAYOUT["He"] = (0, 18)

_LAYOUT["Li"] = (1, 1)
_LAYOUT["Be"] = (1, 2)
_LAYOUT["B"] = (1, 13)
_LAYOUT["C"] = (1, 14)
_LAYOUT["N"] = (1, 15)
_LAYOUT["O"] = (1, 16)
_LAYOUT["F"] = (1, 17)
_LAYOUT["Ne"] = (1, 18)

_LAYOUT["Na"] = (2, 1)
_LAYOUT["Mg"] = (2, 2)
_LAYOUT["Al"] = (2, 13)
_LAYOUT["Si"] = (2, 14)
_LAYOUT["P"] = (2, 15)
_LAYOUT["S"] = (2, 16)
_LAYOUT["Cl"] = (2, 17)
_LAYOUT["Ar"] = (2, 18)

_LAYOUT["K"] = (3, 1)
_LAYOUT["Ca"] = (3, 2)
_LAYOUT["Sc"] = (3, 3)
_LAYOUT["Ti"] = (3, 4)
_LAYOUT["V"] = (3, 5)
_LAYOUT["Cr"] = (3, 6)
_LAYOUT["Mn"] = (3, 7)
_LAYOUT["Fe"] = (3, 8)
_LAYOUT["Co"] = (3, 9)
_LAYOUT["Ni"] = (3, 10)
_LAYOUT["Cu"] = (3, 11)
_LAYOUT["Zn"] = (3, 12)
_LAYOUT["Ga"] = (3, 13)
_LAYOUT["Ge"] = (3, 14)
_LAYOUT["As"] = (3, 15)
_LAYOUT["Se"] = (3, 16)
_LAYOUT["Br"] = (3, 17)
_LAYOUT["Kr"] = (3, 18)

_LAYOUT["Rb"] = (4, 1)
_LAYOUT["Sr"] = (4, 2)
_LAYOUT["Y"] = (4, 3)
_LAYOUT["Zr"] = (4, 4)
_LAYOUT["Nb"] = (4, 5)
_LAYOUT["Mo"] = (4, 6)
_LAYOUT["Tc"] = (4, 7)
_LAYOUT["Ru"] = (4, 8)
_LAYOUT["Rh"] = (4, 9)
_LAYOUT["Pd"] = (4, 10)
_LAYOUT["Ag"] = (4, 11)
_LAYOUT["Cd"] = (4, 12)
_LAYOUT["In"] = (4, 13)
_LAYOUT["Sn"] = (4, 14)
_LAYOUT["Sb"] = (4, 15)
_LAYOUT["Te"] = (4, 16)
_LAYOUT["I"] = (4, 17)
_LAYOUT["Xe"] = (4, 18)

_LAYOUT["Cs"] = (5, 1)
_LAYOUT["Ba"] = (5, 2)
_LAYOUT["Hf"] = (5, 4)
_LAYOUT["Ta"] = (5, 5)
_LAYOUT["W"] = (5, 6)
_LAYOUT["Re"] = (5, 7)
_LAYOUT["Os"] = (5, 8)
_LAYOUT["Ir"] = (5, 9)
_LAYOUT["Pt"] = (5, 10)
_LAYOUT["Au"] = (5, 11)
_LAYOUT["Hg"] = (5, 12)
_LAYOUT["Tl"] = (5, 13)
_LAYOUT["Pb"] = (5, 14)
_LAYOUT["Bi"] = (5, 15)
_LAYOUT["Po"] = (5, 16)
_LAYOUT["At"] = (5, 17)
_LAYOUT["Rn"] = (5, 18)

_LAYOUT["Fr"] = (6, 1)
_LAYOUT["Ra"] = (6, 2)
_LAYOUT["Rf"] = (6, 4)
_LAYOUT["Db"] = (6, 5)
_LAYOUT["Sg"] = (6, 6)
_LAYOUT["Bh"] = (6, 7)
_LAYOUT["Hs"] = (6, 8)
_LAYOUT["Mt"] = (6, 9)
_LAYOUT["Ds"] = (6, 10)
_LAYOUT["Rg"] = (6, 11)
_LAYOUT["Cn"] = (6, 12)
_LAYOUT["Nh"] = (6, 13)
_LAYOUT["Fl"] = (6, 14)
_LAYOUT["Mc"] = (6, 15)
_LAYOUT["Lv"] = (6, 16)
_LAYOUT["Ts"] = (6, 17)
_LAYOUT["Og"] = (6, 18)

_LAYOUT["La"] = (8, 4)
_LAYOUT["Ce"] = (8, 5)
_LAYOUT["Pr"] = (8, 6)
_LAYOUT["Nd"] = (8, 7)
_LAYOUT["Pm"] = (8, 8)
_LAYOUT["Sm"] = (8, 9)
_LAYOUT["Eu"] = (8, 10)
_LAYOUT["Gd"] = (8, 11)
_LAYOUT["Tb"] = (8, 12)
_LAYOUT["Dy"] = (8, 13)
_LAYOUT["Ho"] = (8, 14)
_LAYOUT["Er"] = (8, 15)
_LAYOUT["Tm"] = (8, 16)
_LAYOUT["Yb"] = (8, 17)
_LAYOUT["Lu"] = (8, 18)

_LAYOUT["Ac"] = (9, 4)
_LAYOUT["Th"] = (9, 5)
_LAYOUT["Pa"] = (9, 6)
_LAYOUT["U"] = (9, 7)
_LAYOUT["Np"] = (9, 8)
_LAYOUT["Pu"] = (9, 9)
_LAYOUT["Am"] = (9, 10)
_LAYOUT["Cm"] = (9, 11)
_LAYOUT["Bk"] = (9, 12)
_LAYOUT["Cf"] = (9, 13)
_LAYOUT["Es"] = (9, 14)
_LAYOUT["Fm"] = (9, 15)
_LAYOUT["Md"] = (9, 16)
_LAYOUT["No"] = (9, 17)
_LAYOUT["Lr"] = (9, 18)

_COLS = range(1, 19)
_ROWS = ["i", "ii", "iii", "iv", "v", "vi", "vii"]

# Dictionary that maps the chemical family with a RGB color.
_FAMILY = {
    "default": (128, 128, 128),
    "user-defined": (255, 255, 255),
    "non metal": (153, 255, 153),
    "noble gas": (192, 255, 255),
    "alkali metal": (255, 153, 153),
    "alkaline earth metal": (255, 222, 173),
    "metalloid": (204, 204, 153),
    "halogen": (255, 255, 153),
    "post-transition metal": (204, 204, 204),
    "transition metal": (255, 192, 192),
    "lanthanoid": (255, 191, 255),
    "actinoid": (255, 153, 254),
}

# Dictionary that maps the chemical state with a RGB color.
_STATE = {
    "default": (128, 128, 128),
    "user-defined": (255, 0, 0),
    "gas": (255, 0, 0),
    "liquid": (0, 0, 255),
    "solid": (0, 0, 0),
    "unknown": (0, 150, 0),
}


class QHLine(QFrame):
    """A placeholder GUI element. Draws a horizontal line."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class PopupTextbox(QDialog):
    """A simple dialog displaying text information about a specific
    chemical isotope.
    """

    def __init__(self, *args, input_text="", **kwargs):
        super().__init__(*args, **kwargs)

        self.setStyleSheet("font-family: Courier New;")
        self.text_to_show = input_text
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # self.mainpart = QTextEdit(self)
        # self.mainpart.append(self.text_to_show)
        temp = QLabel(input_text, self)
        # layout.addWidget(self.mainpart)
        layout.addWidget(temp)

        self.setWindowTitle("Element information summary")
        self.show()
        # self.mainpart.resize(QSize(300,500))


class ElementButton(QToolButton):
    """Subclassed from QToolButton, this object shows the name of a
    chemical element, and creates a pop-up menu giving access to information
    about isotopes when clicked.
    """

    atom_info = Signal(object)
    isotope_info = Signal(str)

    def __init__(self, *args, element="Xx", **kwargs):
        super().__init__(*args, **kwargs)

        self.info = ATOMS_DATABASE[element]
        self.setText(element)
        self.setGroupStyleSheet()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.isotopes = [element]

        for iso in sorted(ATOMS_DATABASE.get_isotopes(element)):
            self.isotopes.append(iso)

        self.clicked.connect(self.altContextMenu)
        self.isotope_info.connect(self.popIstopeInfo)

    @Slot()
    def setGroupStyleSheet(self):
        rgb = _FAMILY[self.info["family"]]
        text_rgb = ",".join([str(int(x)) for x in rgb])
        varbox_stylesheet = (
            "QToolButton {background-color:rgb("
            + text_rgb
            + "); font-size: 20pt ; font-weight: bold; font: ; color: rgb(20,0,0)}"
        )
        self.setStyleSheet(varbox_stylesheet)

    def enterEvent(self, a0: QEnterEvent) -> None:
        self.atom_info.emit(self.info)
        return super().enterEvent(a0)

    def populateMenu(self, menu: QMenu):
        for iso in self.isotopes:
            menu.addAction(iso)

    def altContextMenu(self):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(self.mapToGlobal(QPoint(10, 10)))
        if res is not None:
            self.isotope_info.emit(res.text())

    @Slot(str)
    def popIstopeInfo(self, isotope: str):
        infotext = atom_info(isotope, database=ATOMS_DATABASE)
        PopupTextbox(self, input_text=infotext)

    def contextMenuEvent(self, event):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(event.globalPos())
        if res is not None:
            self.isotope_info.emit(res.text())


class InfoDisplay(QFrame):
    """A field embedded in the periodic table of elements.
    Displays information about the chemical elements that the mouse cursor
    is hovering over.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base = QWidget(self)
        layout = QGridLayout(self.base)
        self.setLayout(layout)

        tooltips = [
            "Atomic number",
            "Symbol",
            "Group,Period,Block",
            "Atom",
            "Chemical family",
            "Electron configuration",
            "Relative atomic mass (Da)",
            "Electronegativity",
            "Electron affinity (eV)",
            "Ionization energy (eV)",
        ]

        fields = []
        for n in range(10):
            temp = QLabel(self.base)
            fields.append(temp)
            temp.setToolTip(tooltips[n])
        # in the end it was not necessary to have field[0]
        layout.addWidget(fields[1], 0, 0)
        layout.addWidget(fields[2], 1, 0, 1, 4)  # rowspan, columnspan
        layout.addWidget(fields[3], 3, 0)
        for n in range(4, 10):
            layout.addWidget(fields[n], n - 4, 4)

        self.fields = fields

        stylesheet = "font-weight: bold"
        self.setStyleSheet(stylesheet)

    @Slot(object)
    def updateDisplay(self, info_object):
        # self.fields[0].setText(str(info_object["proton"]))
        self.fields[1].setText(
            "<sup>" + str(info_object["proton"]) + "</sup>" + str(info_object["symbol"])
        )
        self.fields[2].setText(
            f"{str(info_object['group']):2s},{info_object['period']},{info_object['block']}",
        )
        self.fields[3].setText(str(info_object["element"]))
        self.fields[4].setText(str(info_object["family"]))
        self.fields[5].setText(str(info_object["configuration"]))
        self.fields[6].setText(
            "atomic weight = " + str(info_object["atomic_weight"]) + " amu"
        )
        self.fields[7].setText(
            "electronegativity = " + str(info_object["electronegativity"])
        )
        self.fields[8].setText(
            "electron_affinity = " + str(info_object["electron_affinity"]) + " eV"
        )
        self.fields[9].setText(
            "ionization energy = " + str(info_object["ionization_energy"]) + " eV"
        )


class PeriodicTableViewer(QDialog):
    """A widget displaying the periodic table of elements.
    Can be used within MDANSE, or as a standalone program.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Periodic Table of Elements")

        self.glayout = QGridLayout(self)
        self.setLayout(self.glayout)

        self.data_display = InfoDisplay(self)

        self.glayout.addWidget(self.data_display, 1, 5, 3, 8)

        self.placeElements()

    def placeElements(self):
        for key, value in _LAYOUT.items():
            element = ElementButton(self, element=key)
            element.atom_info.connect(self.data_display.updateDisplay)
            row, column = value[0] + 1, value[1] + 1
            self.glayout.addWidget(element, row, column)

        for col_num in range(18):
            self.glayout.addWidget(
                QLabel(str(col_num + 1), self),
                0,
                col_num + 2,
                alignment=Qt.AlignmentFlag.AlignCenter,
            )

        for row_num in range(7):
            self.glayout.addWidget(
                QLabel(_ROWS[row_num], self),
                row_num + 1,
                0,
                alignment=Qt.AlignmentFlag.AlignCenter,
            )

        # now some simple placeholders
        onestar_start = QLabel(self, text="*", alignment=Qt.AlignmentFlag.AlignCenter)
        onestar_end = QLabel(self, text="*", alignment=Qt.AlignmentFlag.AlignCenter)
        twostar_start = QLabel(self, text="**", alignment=Qt.AlignmentFlag.AlignCenter)
        twostar_end = QLabel(self, text="**", alignment=Qt.AlignmentFlag.AlignCenter)
        self.glayout.addWidget(onestar_start, 6, 4)
        self.glayout.addWidget(twostar_start, 7, 4)
        self.glayout.addWidget(onestar_end, 9, 4)
        self.glayout.addWidget(twostar_end, 10, 4)

        self.glayout.addWidget(QHLine(self), 8, 0, 1, 20)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = PeriodicTableViewer()
    root.show()
    app.exec()
