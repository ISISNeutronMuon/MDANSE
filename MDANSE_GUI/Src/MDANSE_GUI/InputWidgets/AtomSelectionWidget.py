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

import json
from enum import Enum

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewerWithPicking
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D
from MDANSE_GUI.Widgets.SelectionWidgets import (
    AllAtomSelection,
    AtomSelection,
    IndexSelection,
    LabelSelection,
    MoleculeSelection,
    PatternSelection,
    PositionSelection,
    SphereSelection,
)


class SelectionValidity(Enum):
    """Strings for selection check results."""

    VALID_SELECTION = "Valid selection"
    USELESS_SELECTION = "Selection did not change. This operation is not needed."
    MALFORMED_SELECTION = "This is not a valid selection string."


class SelectionModel(QStandardItemModel):
    """Stores the selection operations in the GUI view."""

    selection_changed = Signal()

    def __init__(self, trajectory):
        """Assign the current trajectory to the model."""
        super().__init__(None)
        self._trajectory = trajectory
        self._selection = ReusableSelection()
        self._current_selection = set()

    def rebuild_selection(self, last_operation: str) -> SelectionValidity:
        """Update the current selection based on the text in the GUI.

        Parameters
        ----------
        last_operation : str
            Additional selection operation input by the user.

        Returns
        -------
        SelectionValidity
            Result of the check on last_operation.
        """
        self._selection = ReusableSelection()
        self._current_selection = set()
        total_dict = {}
        for row in range(self.rowCount()):
            index = self.index(row, 0)
            item = self.itemFromIndex(index)
            json_string = item.text()
            total_dict[row] = json.loads(json_string)
        self._selection.load_from_json(json.dumps(total_dict))
        self._current_selection = self._selection.select_in_trajectory(self._trajectory)
        if last_operation:
            try:
                valid = self._selection.validate_selection_string(
                    last_operation,
                    self._trajectory,
                    self._current_selection,
                )
            except json.JSONDecodeError:
                return SelectionValidity.MALFORMED_SELECTION
            if valid:
                self._selection.load_from_json(json_string)
                return SelectionValidity.VALID_SELECTION
            return SelectionValidity.USELESS_SELECTION
        return None

    def current_selection(self, last_operation: str = "") -> set[int]:
        """Return the selected atom indices.

        Parameters
        ----------
        last_operation : str, optional
            Extra selection operation typed by the user, by default ""

        Returns
        -------
        set[int]
            indices of all the selected atoms

        """
        self.rebuild_selection(last_operation)
        return self._selection.select_in_trajectory(self._trajectory)

    def current_steps(self) -> str:
        """Return selection operations as a JSON string.

        Returns
        -------
        str
            one string with all the selection operations in sequence

        """
        result = {}
        for row in range(self.rowCount()):
            index = self.index(row, 0)
            item = self.itemFromIndex(index)
            json_string = item.text()
            python_object = json.loads(json_string)
            result[row] = python_object
        return json.dumps(result)

    @Slot(str)
    def accept_from_widget(self, json_string: str):
        """Add a selection operation sent from a selection widget."""
        new_item = QStandardItem(json_string)
        new_item.setEditable(False)
        self.appendRow(new_item)
        self.selection_changed.emit()


class SelectionHelper(QDialog):
    """Generates a string that specifies the atom selection.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.

    """

    _helper_title = "Atom selection helper"

    def __init__(
        self,
        traj_data: tuple[str, Trajectory],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """Create the selection dialog.

        Parameters
        ----------
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.

        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)

        self.trajectory = traj_data[1]
        self.system = self.trajectory.chemical_system
        self.selection_model = SelectionModel(self.trajectory)
        self._field = field
        self.atm_full_names = self.system.name_list
        self.molecule_names = self.system.unique_molecules()
        self.labels = list(map(str, self.system._labels))

        self.selection_textbox = QPlainTextEdit()
        self.selection_textbox.setReadOnly(True)

        mol_view = MolecularViewerWithPicking()
        mol_view.picked_atoms_changed.connect(self.update_from_3d_view)
        self.view_3d = View3D(mol_view)
        self.view_3d.update_panel(traj_data)

        layouts = self.create_layouts()

        bottom = QHBoxLayout()
        for button in self.create_buttons():
            bottom.addWidget(button)

        helper_layout = QHBoxLayout()
        sub_layout = QVBoxLayout()
        helper_layout.addLayout(layouts[0])
        helper_layout.addLayout(sub_layout)
        for layout in layouts[1:]:
            sub_layout.addLayout(layout)
        sub_layout.addLayout(bottom)

        self.setLayout(helper_layout)

        self.all_selection = True
        self.selected = set()
        self.reset()

    def closeEvent(self, a0):
        """Hide the window instead of closing.

        Some issues occur in the
        3D viewer when it is closed and then reopened.
        """
        a0.ignore()
        self.hide()

    def create_buttons(self) -> list[QPushButton]:
        """Add buttons to the dialog layout.

        Returns
        -------
        list[QPushButton]
            List of push buttons to add to the last layout from
            create_layouts.

        """
        apply = QPushButton("Use Setting")
        reset = QPushButton("Reset")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        reset.clicked.connect(self.reset)
        close.clicked.connect(self.close)
        return [apply, reset, close]

    def create_layouts(self) -> list[QVBoxLayout]:
        """Call functions creating other widgets.

        Returns
        -------
        list[QVBoxLayout]
            List of QVBoxLayout to add to the helper layout.

        """
        layout_3d = QVBoxLayout()
        layout_3d.addWidget(self.view_3d)

        left = QVBoxLayout()
        for widget in self.left_widgets():
            left.addWidget(widget)

        right = QHBoxLayout()
        for widget in self.right_widgets():
            right.addWidget(widget)

        return [layout_3d, left, right]

    def right_widgets(self) -> list[QWidget]:
        """Create widgets visualising the selection results.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the right layout from
            create_layouts.

        """
        return [self.selection_operations_view, self.selection_textbox]

    def left_widgets(self) -> list[QWidget]:
        """Create widgets for defining the selection.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the left layout from
            create_layouts.

        """
        select = QGroupBox("selection")
        select_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidget(select)
        scroll_area.setWidgetResizable(True)

        self.selection_widgets = [
            AllAtomSelection(self),
            AtomSelection(self, self.trajectory),
            IndexSelection(self),
            MoleculeSelection(self, self.trajectory),
            PatternSelection(self),
            LabelSelection(self, self.trajectory),
            PositionSelection(self, self.trajectory, self.view_3d._viewer),
            SphereSelection(self, self.trajectory, self.view_3d._viewer),
        ]

        for widget in self.selection_widgets:
            select_layout.addWidget(widget)
            widget.new_selection.connect(self.selection_model.accept_from_widget)

        invert_layout = QHBoxLayout()
        label = QLabel("Current selection:")
        self.selection_line = QLineEdit("", self)
        apply = QPushButton("Apply")
        apply.clicked.connect(self.append_selection)
        invert_layout.addWidget(label)
        invert_layout.addWidget(self.selection_line)
        invert_layout.addWidget(apply)
        select_layout.addLayout(invert_layout)

        select.setLayout(select_layout)

        self.selection_operations_view = QListView(self)
        self.selection_operations_view.setModel(self.selection_model)
        self.selection_model.selection_changed.connect(self.recalculate_selection)
        return [scroll_area]

    @Slot()
    def recalculate_selection(self):
        """Update atom indices after selection change."""
        self.selected = self.selection_model.current_selection()
        self.view_3d._viewer.change_picked(self.selected)
        self.update_selection_textbox()

    def update_from_3d_view(self, _selection: set[int]) -> None:
        """Update atom indices after an atom has been clicked.

        A selection/deselection was made in the 3d view, update the
        check_boxes, combo_boxes and textbox.

        Parameters
        ----------
        selection : set[int]
            Selection indexes from the 3d view.

        """
        self.update_selection_textbox()

    @Slot()
    def append_selection(self):
        """Add a selection operation from the text input field."""
        self.selection_line.setStyleSheet("")
        self.selection_line.setToolTip("")
        selection_text = self.selection_line.text()
        validation = self.selection_model.rebuild_selection(selection_text)
        if validation in (
            SelectionValidity.MALFORMED_SELECTION,
            SelectionValidity.USELESS_SELECTION,
        ):
            self.selection_line.setStyleSheet(
                "QWidget#InputWidget { background-color:rgb(180,20,180); font-weight: bold }"
            )
            self.selection_line.setToolTip(validation)
        elif validation == SelectionValidity.VALID_SELECTION:
            self.selection_model.appendRow(QStandardItem(selection_text))
            self.view_3d._viewer.change_picked(self.selected)
            self.update_selection_textbox()

    def update_selection_textbox(self) -> None:
        """Update the selection textbox."""
        num_sel = len(self.selected)
        text = [f"Number of atoms selected:\n{num_sel}\n\nSelected atoms:\n"]
        for idx in self.selected:
            text.append(f"{idx}  ({self.atm_full_names[idx]})\n")
        self.selection_textbox.setPlainText("".join(text))

    def apply(self) -> None:
        """Send the selection from the dialog to the main widget."""
        self._field.setText(self.selection_model.current_steps())

    def reset(self) -> None:
        """Reset the helper to the default state."""
        self.selection_model.clear()
        self.selection_model.accept_from_widget(
            '{"function_name": "select_all", "operation_type": "union"}'
        )
        self.recalculate_selection()


class AtomSelectionWidget(WidgetBase):
    """The atoms selection widget."""

    _push_button_text = "Atom selection helper"
    _default_value = "{}"
    _tooltip_text = "Specify which atoms will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."

    def __init__(self, *args, **kwargs):
        """Create the main widget for atom selection."""
        super().__init__(*args, **kwargs)
        self._value = self._default_value
        self._field = QLineEdit(self._default_value, self._base)
        self._field.setPlaceholderText(self._default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        self._field.textChanged.connect(self.updateValue)
        traj_config = self._configurator._configurable[
            self._configurator._dependencies["trajectory"]
        ]
        traj_filename = traj_config["filename"]
        trajectory = traj_config["instance"]
        self.helper = self.create_helper((traj_filename, trajectory))
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(self._tooltip_text)

    def create_helper(
        self,
        traj_data: tuple[str, Trajectory],
    ) -> SelectionHelper:
        """Create the selection dialog.

        It will be populated with selection widget which can be used
        to create the complete atom selection string.

        Parameters
        ----------
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        SelectionHelper
            Create and return the selection helper QDialog.

        """
        return SelectionHelper(traj_data, self._field, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Open the helper dialog."""
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
        else:
            if hasattr(self.helper, "previous_geometry"):
                self.helper.restoreGeometry(self.helper.previous_geometry)
            self.helper.show()

    def get_widget_value(self) -> str:
        """Return the current text in the input field.

        Returns
        -------
        str
            The JSON selector setting.

        """
        selection_string = self._field.text()
        if len(selection_string) < 1:
            self._empty = True
            return self._default_value
        self._empty = False
        return selection_string
