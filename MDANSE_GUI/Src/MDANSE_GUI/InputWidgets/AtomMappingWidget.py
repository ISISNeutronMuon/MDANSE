# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/InputWidgets/AtomMappingWidget.py
# @brief     Implements module/class/test AtomMappingWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
import json
from collections import defaultdict

from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
)

from MDANSE.Framework.AtomMapping import guess_element
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.FileWithAtomDataConfigurator import (
    FileWithAtomDataConfigurator,
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget


class AtomMappingHelperDialog(QDialog):
    """The atom mapping helper dialog used to help generate the atom
    map setting JSON string.
    """

    def __init__(
        self, field_widget: InputFileWidget, field: QLineEdit, parent, *args, **kwargs
    ):
        """
        Parameters
        ----------
        field_widget: InputFileWidget
            The input file widget which is used to obtain the group and
            atom labels.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Atom mapping helper")
        self.min_width = kwargs.get("min_width", 450)
        self.resize(self.min_width, self.height())
        self.setMinimumWidth(self.min_width)
        self._field = field

        self._file_widget = field_widget
        self._file_widget._field.textChanged.connect(self.update_helper)

        self.layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Group Label"))
        header_layout.addWidget(QLabel("Atom Label"))
        header_layout.addWidget(QLabel("Element"))

        self.mapping_widgets = []
        self.mapping_layout = QGridLayout()

        button_layout = QHBoxLayout()
        apply = QPushButton("Apply")
        auto = QPushButton("Auto Fill")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        auto.clicked.connect(self.auto_fill)
        close.clicked.connect(self.close)
        button_layout.addWidget(apply)
        button_layout.addWidget(auto)
        button_layout.addWidget(close)

        self.layout.addLayout(header_layout)
        self.layout.addLayout(self.mapping_layout)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.all_symbols = ATOMS_DATABASE.atoms

    def update_helper(self) -> None:
        """Get the atoms labels from the file widget and add mapping
        widgets to the helper.
        """
        self.clear_panel()
        if not self._file_widget._configurator.valid:
            return

        labels = self._file_widget._configurator.get_atom_labels()
        for i, label in enumerate(labels):
            w0 = QLabel(label.grp_label)
            w1 = QLabel(label.atm_label)
            w2 = QComboBox()
            w2.addItems(self.all_symbols)
            self.mapping_widgets.append((w0, w1, w2))
            self.mapping_layout.addWidget(w0, i, 0)
            self.mapping_layout.addWidget(w1, i, 1)
            self.mapping_layout.addWidget(w2, i, 2)

        self.auto_fill()

    def clear_panel(self) -> None:
        """Clear the widgets so that it leaves an empty mapping
        layout.
        """
        for ws in self.mapping_widgets:
            for w in ws:
                w.setParent(None)
                self.mapping_layout.removeWidget(w)
        self.mapping_widgets = []

    def auto_fill(self) -> None:
        """Autofill the comboboxes using a simple guess."""
        for _, w1, w2 in self.mapping_widgets:
            try:
                guess = guess_element(w1.text())
                idx = self.all_symbols.index(guess)
                w2.setCurrentIndex(idx)
            except AttributeError:
                w2.setCurrentIndex(-1)

    def apply(self) -> None:
        """Convert the selection in the mapping widgets to a JSON string
        and set the field.
        """
        settings = defaultdict(lambda: dict())
        for w0, w1, w2 in self.mapping_widgets:
            settings[w0.text()][w1.text()] = w2.currentText()
        self._field.setText(json.dumps(settings))


class AtomMappingWidget(WidgetBase):
    """The atom mapping widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = "{}"
        self._value = default_value
        self._field = QLineEdit(default_value, self._base)
        self._field.setPlaceholderText(default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible

        # file input widgets should be loaded into the _widgets list
        # before this one
        for widget in self.parent()._widgets:
            if (
                widget._configurator
                is self._configurator._configurable[
                    self._configurator._dependencies["input_file"]
                ]
            ):
                self._file_widget = widget
                break

        self.helper = AtomMappingHelperDialog(
            self._file_widget, self._field, self._base
        )
        self.helper_button = QPushButton("Atom mapping helper", self._base)
        self.helper_button.clicked.connect(self.helper_dialog)
        self.helper_button.setEnabled(False)
        self._field.textChanged.connect(self.updateValue)
        self._default_value = default_value
        self._layout.addWidget(self._field)
        self._layout.addWidget(self.helper_button)
        self._file_widget._field.textChanged.connect(self.update_helper_button)
        self.update_labels()
        self.updateValue()

    @Slot()
    def update_helper_button(self) -> None:
        """Enables the helper button when the file widget has a valid
        file input.
        """
        if self._file_widget._configurator.valid:
            self.helper_button.setEnabled(True)
        else:
            self.helper_button.setEnabled(False)
        self.helper.apply()

    @Slot()
    def helper_dialog(self) -> None:
        """Opens the helper dialog."""
        if self.helper.isVisible():
            self.helper.close()
        else:
            self.helper.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON string map setting.
        """
        mapping_string = self._field.text()
        if len(mapping_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return mapping_string
