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
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HelperDialog(QDialog):
    """Generates a string that specifies the atom selection."""

    def __init__(self, selector, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.selector = selector
        full_settings = self.selector.full_settings

        checkbox_text = {
            "all": "all atoms",
            "hs_on_heteroatom": "hydrogen atoms on heteroatoms",
            "primary_amine": "primary amine group atoms",
            "hydroxy": "hydroxy group atoms",
            "methyl": "methyl group atoms",
            "phosphate": "phosphate group atoms",
            "sulphate": "sulphate group atoms",
            "thiol": "thiol group atoms",
            "water": "water molecule atoms",
            "invert": "invert the selection"
        }

        layout = QVBoxLayout()

        select = QGroupBox("selection")
        select_layout = QVBoxLayout()
        invert = QGroupBox("inversion")
        invert_layout = QVBoxLayout()

        for k, v in full_settings.items():
            if isinstance(v, bool):
                checkbox = QCheckBox()
                checkbox.setText(checkbox_text[k])
                checkbox.setChecked(v)
                if k == "invert":
                    invert_layout.addWidget(checkbox)
                else:
                    select_layout.addWidget(checkbox)
            elif isinstance(v, dict):
                combo = QComboBox()
                combo.addItems(v.keys())
                combo.setCurrentIndex(-1)
                select_layout.addWidget(combo)

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
        browse_button = QPushButton("atom selection helper", self._base)
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
