# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/AtomSelectionWidget.py
# @brief     Implements module/class/test AtomSelectionWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HelperDialog(QDialog):
    """Generates a string that specifies the atom selection."""

    def __init__(self, selector, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Atom selection helper")
        self.selector = selector
        full_settings = self.selector.full_settings
        match_exists = self.selector.match_exists

        cbox_text = {
            "all": "All atoms:",
            "hs_on_heteroatom": "Hs on heteroatoms:",
            "primary_amine": "Primary amine groups:",
            "hydroxy": "Hydroxy groups:",
            "methyl": "Methyl groups:",
            "phosphate": "Phosphate groups:",
            "sulphate": "Sulphate groups:",
            "thiol": "Thiol groups:",
            "water": "Water molecules:",
            "element": "Elements:",
            "hs_on_element": "Hs on element:",
            "index": "Index:",
            "invert": "Invert the selection:"
        }

        layout = QVBoxLayout()

        select = QGroupBox("selection")
        select_layout = QVBoxLayout()
        invert = QGroupBox("inversion")
        invert_layout = QVBoxLayout()

        for k, v in full_settings.items():

            if isinstance(v, bool):
                check_layout = QHBoxLayout()
                checkbox = QCheckBox()
                checkbox.setChecked(v)
                checkbox.setLayoutDirection(Qt.RightToLeft)
                label = QLabel(cbox_text[k])
                if not match_exists[k]:
                    checkbox.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                check_layout.addWidget(label)
                check_layout.addWidget(checkbox)
                if k == "invert":
                    invert_layout.addLayout(check_layout)
                else:
                    select_layout.addLayout(check_layout)

            elif isinstance(v, dict):
                combo_layout = QHBoxLayout()
                combo = QComboBox()
                items = [i for i in v.keys() if match_exists[k][i]]
                combo.addItems(items)
                combo.setCurrentIndex(-1)
                label = QLabel(cbox_text[k])
                if len(items) == 0:
                    combo.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                combo_layout.addWidget(label)
                combo_layout.addWidget(combo)
                select_layout.addLayout(combo_layout)

        select.setLayout(select_layout)
        invert.setLayout(invert_layout)
        layout.addWidget(select)
        layout.addWidget(invert)

        bottom = QHBoxLayout()
        apply = QPushButton("Apply")
        cancel = QPushButton("Cancel")
        bottom.addWidget(apply)
        bottom.addWidget(cancel)

        layout.addLayout(bottom)
        self.setLayout(layout)


class AtomSelectionWidget(WidgetBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = '{"all": true}'
        self.selector = self._configurator.get_selector()
        self.helper = HelperDialog(self.selector, self.parent())
        self._value = default_value
        self.field = QLineEdit(default_value, self._base)
        browse_button = QPushButton("Atom selection helper", self._base)
        browse_button.clicked.connect(self.helper_dialog)
        self.field.textChanged.connect(self.check_valid_field)
        self._layout.addWidget(self.field)
        self._layout.addWidget(browse_button)
        self.update_labels()

    def helper_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        self.helper.show()

    def check_valid_field(self, value):
        if self.selector.check_valid_json_settings(value):
            self.field.setStyleSheet("color: black;")
        else:
            self.field.setStyleSheet("color: red;")

    def get_widget_value(self):
        selection_string = self.field.text()
        return selection_string
