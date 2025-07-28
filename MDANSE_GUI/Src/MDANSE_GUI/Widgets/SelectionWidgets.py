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

import json
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)
from rdkit.Chem import MolFromSmarts

from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.CheckableComboBox import CheckableComboBox

if TYPE_CHECKING:
    from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewer


class IndexSelectionMode(Enum):
    """Valid atom selection modes for select_atoms."""

    LIST = "list"
    RANGE = "range"
    SLICE = "slice"

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


class XYZValidator(QValidator):
    """A custom validator for a QLineEdit.

    It is intended to limit the input to a string
    of 3 comma-separated float numbers.

    Additional checks are necessary later in the code,
    since the validator cannot exclude the cases of
    1 or 2 comma-separated values, since they are
    a preliminary step when typing in 3 numbers.
    """

    PARAMETERS_NEEDED = 3

    def validate(self, input_string: str, position: int) -> tuple[int, str]:
        """Check the input string from a widget.

        Implementation of the virtual method of QValidator.
        It takes in the string from a QLineEdit and the cursor position,
        and an enum value of the validator state. Widgets will reject
        inputs which change the state to Invalid.

        Parameters
        ----------
        input_string : str
            current contents of a text input field
        position : int
            position of the cursor in the text input field

        Returns
        -------
        int
            Validator state.
        str
            Original input string.
        int
            Cursor position.

        """
        state = QValidator.State.Intermediate
        comma_count = input_string.count(",")
        if input_string:
            try:
                values = [float(x) for x in input_string.split(",")]
            except (TypeError, ValueError):
                if input_string.endswith(",") and comma_count < self.PARAMETERS_NEEDED:
                    state = QValidator.State.Intermediate
                else:
                    state = QValidator.State.Invalid
            else:
                if len(values) > self.PARAMETERS_NEEDED:
                    state = QValidator.State.Invalid
                elif len(values) == self.PARAMETERS_NEEDED:
                    state = QValidator.State.Acceptable
                else:
                    state = QValidator.State.Intermediate
        return state, input_string, position


class BasicSelectionWidget(QGroupBox):
    """Base class for atom selection widgets."""

    new_selection = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        widget_label: str = "Atom selection widget",
        add_standard_widgets: bool = True,
    ):
        """Create subwidgets common to atom selection.

        Parameters
        ----------
        parent : QWidget, optional
            parent in the Qt hierarchy, by default None
        widget_label : str, optional
            Text shown above the widget, by default "Atom selection widget"
        add_standard_widgets: bool, optional
            if True, the operation type combo box and apply button appead in the widget

        """
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.setTitle(widget_label)
        self.add_specific_widgets()
        if add_standard_widgets:
            self.add_standard_widgets()

    def parameter_dictionary(self) -> dict[str, Any]:
        """Collect and return selection function parameters."""
        return {}

    def add_specific_widgets(self):
        """Add additional widgets to layout, depending on the selection function."""
        return

    def add_standard_widgets(self):
        """Create widgets needed by all atom selection types.

        This creates a combo box for the set operation type,
        and a button for making the selection.
        """
        self.mode_box = QComboBox(self)
        self.mode_box.setEditable(False)
        self.mode_box.addItems(
            ["Add (union)", "Filter (intersection)", "Remove (difference)"],
        )
        self._mode_box_values = ["union", "intersection", "difference"]
        self.commit_button = QPushButton("Apply", self)
        layout = self.layout()
        layout.addWidget(self.mode_box)
        layout.addWidget(self.commit_button)
        self.commit_button.clicked.connect(self.create_selection)

    def get_mode(self) -> str:
        """Get the current set operation type from the combo box."""
        return self._mode_box_values[self.mode_box.currentIndex()]

    def create_selection(self):
        """Collect the input values and emit them in a signal."""
        funtion_parameters = self.parameter_dictionary()
        funtion_parameters["operation_type"] = self.get_mode()
        self.new_selection.emit(json.dumps(funtion_parameters))


class GUISelection(BasicSelectionWidget):
    """Widget for confirming and cancelling manual selection in 3D view."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        widget_label: str = "Manual Selection",
    ):
        """Pass inputs to the parent class init.

        Parameters
        ----------
        parent : QWidget, optional
            parent in the Qt hierarchy, by default None
        widget_label : str, optional
            Text over the widget, by default "ALL ATOMS"

        """
        super().__init__(parent, widget_label=widget_label, add_standard_widgets=False)

    def add_specific_widgets(self) -> None:
        """Add GUI selection buttons, not connected."""
        layout = self.layout()
        self.confirm_gui_selection = QPushButton("CONFIRM manual selection", self)
        self.undo_gui_selection = QPushButton("Undo GUI selection", self)
        for button in [self.confirm_gui_selection, self.undo_gui_selection]:
            layout.addWidget(button)


class AllAtomSelection(BasicSelectionWidget):
    """Widget for global atom selection, e.g. all atoms, no atoms."""

    def __init__(self, parent=None, widget_label="ALL ATOMS"):
        """Pass inputs to the parent class init.

        Parameters
        ----------
        parent : QWidget, optional
            parent in the Qt hierarchy, by default None
        widget_label : str, optional
            Text over the widget, by default "ALL ATOMS"

        """
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Add the INVERT button."""
        layout = self.layout()
        inversion_button = QPushButton("INVERT selection", self)
        inversion_button.clicked.connect(self.invert_selection)
        layout.addWidget(inversion_button)
        layout.addWidget(QLabel("Add/remove ALL atoms"))

    def invert_selection(self):
        """Emit the string for inverting the selection."""
        self.new_selection.emit(json.dumps({"function_name": "invert_selection"}))

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        return {"function_name": "select_all"}


class AtomSelection(BasicSelectionWidget):
    """GUI frontend for select_atoms."""

    def __init__(
        self,
        parent=None,
        trajectory: Trajectory = None,
        widget_label="Select atoms",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        trajectory : Trajectory, optional
            The current trajectory object, by default None
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self.atom_types = []
        self.atom_names = []
        if trajectory:
            self.atom_types = list(np.unique(trajectory.chemical_system.atom_list))
            if trajectory.chemical_system.name_list:
                self.atom_names = list(np.unique(trajectory.chemical_system.name_list))
        self.selection_types = []
        self.selection_keyword = ""
        if self.atom_types:
            self.selection_types += ["type"]
        if self.atom_names:
            self.selection_types += ["name"]
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create selection combo boxes."""
        layout = self.layout()
        layout.addWidget(QLabel("Select atoms by atom"))
        self.selection_type_combo = QComboBox(self)
        self.selection_type_combo.addItems(self.selection_types)
        self.selection_type_combo.setEditable(False)
        layout.addWidget(self.selection_type_combo)
        self.selection_field = CheckableComboBox(self)
        layout.addWidget(self.selection_field)
        self.selection_type_combo.currentTextChanged.connect(self.switch_mode)
        self.selection_type_combo.setCurrentText(self.selection_types[0])
        self.switch_mode(self.selection_types[0])

    @Slot(str)
    def switch_mode(self, new_mode: str):
        """Change the contents of the second combo box."""
        self.selection_field.clear()
        if new_mode == "type":
            self.selection_field.addItems(self.atom_types)
            self.selection_keyword = "atom_types"
        elif new_mode == "name":
            self.selection_field.addItems(self.atom_names)
            self.selection_keyword = "atom_names"

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        function_parameters = {"function_name": "select_atoms"}
        selection = self.selection_field.checked_values()
        function_parameters[self.selection_keyword] = selection
        return function_parameters


class IndexSelection(BasicSelectionWidget):
    """GUI frontend for select_atoms."""

    def __init__(self, parent=None, widget_label="Index selection"):
        """Create all the widgets.

        Parameters
        ----------
        parent : QWidget, optional
            parent in the Qt object hierarchy, by default None
        widget_label : str, optional
            Text shown above the widget, by default "Index selection"

        """
        super().__init__(parent, widget_label=widget_label)
        self.selection_keyword = "index_list"

    def add_specific_widgets(self):
        """Create the combo box and text input field."""
        layout = self.layout()
        layout.addWidget(QLabel("Select atoms by index"))
        self.selection_type_combo = QComboBox(self)
        self.selection_type_combo.addItems(mode.value for mode in IndexSelectionMode)
        self.selection_type_combo.setEditable(False)
        layout.addWidget(self.selection_type_combo)

        self.selection_field = QLineEdit(self)
        layout.addWidget(self.selection_field)
        self.selection_type_combo.currentTextChanged.connect(self.switch_mode)
        # Set default
        self.switch_mode("list")

    @Slot(str)
    def switch_mode(self, new_mode: str):
        """Change the meaning of the text input field."""
        new_mode = IndexSelectionMode(new_mode)
        self.selection_field.setText("")

        if new_mode is IndexSelectionMode.LIST:
            self.selection_field.setPlaceholderText("0,1,2")
            self.selection_keyword = "index_list"
            self.selection_separator = ","
        elif new_mode is IndexSelectionMode.RANGE:
            self.selection_field.setPlaceholderText("0-20")
            self.selection_keyword = "index_range"
            self.selection_separator = "-"
        elif new_mode is IndexSelectionMode.SLICE:
            self.selection_field.setPlaceholderText("first:last:step")
            self.selection_keyword = "index_slice"
            self.selection_separator = ":"

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        function_parameters = {"function_name": "select_atoms"}
        selection = self.selection_field.text()
        function_parameters[self.selection_keyword] = [
            int(x) for x in selection.split(self.selection_separator)
        ]
        return function_parameters


class MoleculeSelection(BasicSelectionWidget):
    """GUI frontend for select_molecule."""

    def __init__(
        self,
        parent=None,
        trajectory: Trajectory = None,
        widget_label="Select molecules",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        trajectory : Trajectory, optional
            The current trajectory object, by default None
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self.molecule_names = []
        if trajectory:
            self.molecule_names = trajectory.chemical_system.unique_molecules()
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create the combo box for molecule names."""
        layout = self.layout()
        layout.addWidget(QLabel("Select molecules named: "))
        self.selection_field = CheckableComboBox(self)
        layout.addWidget(self.selection_field)
        self.selection_field.addItems(self.molecule_names)

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        function_parameters = {"function_name": "select_molecules"}
        selection = self.selection_field.checked_values()
        function_parameters["molecule_names"] = selection
        return function_parameters


class LabelSelection(BasicSelectionWidget):
    """GUI frontend for select_label."""

    def __init__(
        self,
        parent=None,
        trajectory: Trajectory = None,
        widget_label="Select by label",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        trajectory : Trajectory, optional
            The current trajectory object, by default None
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self.labels = []
        if trajectory:
            self.labels = list(trajectory.chemical_system._labels.keys())
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create the combo box for atom labels."""
        layout = self.layout()
        layout.addWidget(QLabel("Select atoms with label: "))
        self.selection_field = CheckableComboBox(self)
        layout.addWidget(self.selection_field)
        self.selection_field.addItems(self.labels)

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        function_parameters = {"function_name": "select_labels"}
        selection = self.selection_field.checked_values()
        function_parameters["atom_labels"] = selection
        return function_parameters


class PatternSelection(BasicSelectionWidget):
    """GUI frontend for select_pattern."""

    def __init__(
        self,
        parent=None,
        widget_label="SMARTS pattern matching",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self.pattern_dictionary = {
            "primary amine": "[#7X3;H2;!$([#7][#6X3][!#6]);!$([#7][#6X2][!#6])](~[H])~[H]",
            "hydroxy": "[#8;H1,H2]~[H]",
            "methyl": "[#6;H3](~[H])(~[H])~[H]",
            "phosphate": "[#15X4](~[#8])(~[#8])(~[#8])~[#8]",
            "sulphate": "[#16X4](~[#8])(~[#8])(~[#8])~[#8]",
            "thiol": "[#16X2;H1]~[H]",
        }
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create the pattern text field."""
        layout = self.layout()
        layout.addWidget(QLabel("Pick a group"))
        self.selection_field = QComboBox(self)
        layout.addWidget(self.selection_field)
        self.selection_field.addItems(self.pattern_dictionary.keys())
        layout.addWidget(QLabel("pattern:"))
        self.input_field = QLineEdit("", self)
        self.input_field.setPlaceholderText("can be edited")
        layout.addWidget(self.input_field)
        self.selection_field.currentTextChanged.connect(self.update_string)
        self.input_field.textChanged.connect(self.check_inputs)

    @Slot()
    def check_inputs(self):
        """Disable selection of invalid or incomplete input."""
        enable = True
        smarts_string = self.input_field.text()
        temp_molecule = MolFromSmarts(smarts_string)
        if temp_molecule is None:
            enable = False
        self.commit_button.setEnabled(enable)

    @Slot(str)
    def update_string(self, key_string: str):
        """Fill the input field with pre-defined text."""
        if key_string in self.pattern_dictionary:
            self.input_field.setText(self.pattern_dictionary[key_string])

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        function_parameters = {"function_name": "select_pattern"}
        selection = self.input_field.text()
        function_parameters["rdkit_pattern"] = selection
        return function_parameters


class PositionSelection(BasicSelectionWidget):
    """GUI frontend for select_positions."""

    N_DIMS = 3

    def __init__(
        self,
        parent=None,
        trajectory: Trajectory = None,
        molecular_viewer: MolecularViewer = None,
        widget_label="Select by position",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        trajectory : Trajectory, optional
            The current trajectory object, by default None
        molecular_viewer : MolecularViewer, optional
            instance of the 3D viewer showing the current simulation frame
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self._viewer = molecular_viewer
        temp_coordinates = trajectory.coordinates(0)
        self._lower_limit = np.min(temp_coordinates, axis=0)
        self._upper_limit = np.max(temp_coordinates, axis=0)

        self._current_lower_limit = self._lower_limit.copy()
        self._current_upper_limit = self._upper_limit.copy()
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create text input fields with validators."""
        layout = self.layout()
        layout.addWidget(QLabel("Lower limits"))
        self._lower_limit_input = QLineEdit(
            ",".join([str(round(x, 3)) for x in self._lower_limit]),
        )
        layout.addWidget(self._lower_limit_input)
        layout.addWidget(QLabel("Upper limits"))
        self._upper_limit_input = QLineEdit(
            ",".join([str(round(x, 3)) for x in self._upper_limit]),
        )
        layout.addWidget(self._upper_limit_input)
        for field in [self._lower_limit_input, self._upper_limit_input]:
            field.setValidator(XYZValidator(self))
            field.textChanged.connect(self.check_inputs)

    @Slot()
    def check_inputs(self):
        """Disable selection of invalid or incomplete input."""
        enable = True
        try:
            self._current_lower_limit = [
                float(x) for x in self._lower_limit_input.text().split(",")
            ]
            self._current_upper_limit = [
                float(x) for x in self._upper_limit_input.text().split(",")
            ]
        except (TypeError, ValueError):
            enable = False
        else:
            if (
                len(self._current_lower_limit) != self.N_DIMS
                or len(self._current_upper_limit) != self.N_DIMS
            ):
                enable = False
        self.commit_button.setEnabled(enable)

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        return {
            "function_name": "select_positions",
            "frame_number": self._viewer._current_frame,
            "position_minimum": list(self._current_lower_limit),
            "position_maximum": list(self._current_upper_limit),
        }


class SphereSelection(BasicSelectionWidget):
    """GUI frontend for select_sphere."""

    N_DIMS = 3

    def __init__(
        self,
        parent=None,
        trajectory: Trajectory = None,
        molecular_viewer: MolecularViewer = None,
        widget_label="Select in a sphere",
    ):
        """Create the widgets for select_atoms.

        Parameters
        ----------
        parent : QWidget, optional
            parent from the Qt object hierarchy, by default None
        trajectory : Trajectory, optional
            The current trajectory object, by default None
        molecular_viewer : MolecularViewer, optional
            instance of the 3D viewer showing the current simulation frame
        widget_label : str, optional
            Text shown over the widget, by default "Select atoms"

        """
        self._viewer = molecular_viewer
        temp_coordinates = trajectory.coordinates(0)
        self._current_sphere_centre = np.mean(temp_coordinates, axis=0)
        self._current_sphere_radius = round(np.min(np.std(temp_coordinates, axis=0)), 3)
        super().__init__(parent, widget_label=widget_label)

    def add_specific_widgets(self):
        """Create the text input fields for sphere radius and centre."""
        layout = self.layout()
        layout.addWidget(QLabel("Sphere centre"))
        self._sphere_centre_input = QLineEdit(
            ",".join([str(round(x, 3)) for x in self._current_sphere_centre]),
            self,
        )
        layout.addWidget(self._sphere_centre_input)
        layout.addWidget(QLabel("Sphere radius (nm)"))
        self._sphere_radius_input = QLineEdit(str(self._current_sphere_radius), self)
        layout.addWidget(self._sphere_radius_input)
        self._sphere_centre_input.setValidator(XYZValidator())
        self._sphere_centre_input.textChanged.connect(self.check_inputs)
        self._sphere_radius_input.setValidator(QDoubleValidator())
        self._sphere_radius_input.textChanged.connect(self.check_inputs)

    @Slot()
    def check_inputs(self):
        """Disable selection on invalid or incomplete input."""
        enable = True
        try:
            self._current_sphere_centre = [
                float(x) for x in self._sphere_centre_input.text().split(",")
            ]
            self._current_sphere_radius = float(self._sphere_radius_input.text())
        except (TypeError, ValueError):
            enable = False
        else:
            if len(self._current_sphere_centre) != self.N_DIMS:
                enable = False
        self.commit_button.setEnabled(enable)

    def parameter_dictionary(self):
        """Collect and return selection function parameters."""
        return {
            "function_name": "select_sphere",
            "frame_number": self._viewer._current_frame,
            "sphere_centre": list(self._current_sphere_centre),
            "sphere_radius": self._current_sphere_radius,
        }
