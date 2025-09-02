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
from pathlib import Path

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QDialog,
    QFileDialog,
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

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewerWithPicking
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D
from MDANSE_GUI.Widgets.SelectionWidgets import (
    AllAtomSelection,
    AtomSelection,
    GUISelection,
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
        self._manual_selection_item = None
        self._clicked_atoms = []

    def clear(self):
        """Remove all the lines from the selection model."""
        self._clicked_atoms = []
        return super().clear()

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

    @Slot(int)
    def on_atom_clicked(self, index: int):
        """Add atom index to manual selection. Receives signals from View3D."""
        if not self._clicked_atoms:
            self._manual_selection_item = QStandardItem("Manual selection IN PROGRESS")
            self.appendRow([self._manual_selection_item])
        self._clicked_atoms.append(index)
        self._manual_selection_item.setText(
            f"Manual selection IN PROGRESS: clicked on {self._clicked_atoms}",
        )

    @Slot()
    def clear_manual_selection(self):
        """Remove the placeholder item from the end of the list, clear clicked atoms."""
        if not self._clicked_atoms:
            return
        if self._manual_selection_item:
            self.removeRow(self.rowCount() - 1)
            self._manual_selection_item = None
        self._clicked_atoms = []

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
        self.finalise_manual_selection()
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

    def finalise_manual_selection(self):
        """Replace the placeholder item with an actual atom selection operation.

        This method commits the changes to selection made by the user in the
        3D view. It should be called before adding a new selection, closing
        the dialog and saving the selection. Optionally, the user can also
        call this method manually with a button.
        """
        if self._clicked_atoms:
            if self._manual_selection_item:
                self.removeRow(self.rowCount() - 1)
                self._manual_selection_item = None
            new_params = {
                "function_name": "toggle_selection",
                "clicked_atoms": self._clicked_atoms,
            }
            json_string = json.dumps(new_params)
            self._clicked_atoms = []
            self.accept_from_widget(json_string)

    @Slot(str)
    def accept_from_widget(self, json_string: str):
        """Add a selection operation sent from a selection widget."""
        self.finalise_manual_selection()
        new_item = QStandardItem(json_string)
        new_item.setEditable(False)
        self.appendRow(new_item)
        self.selection_changed.emit()

    @Slot(str)
    def create_from_string(self, json_string: str):
        """Initialise a new selection from a string."""
        self.clear()
        dictionary = json.loads(json_string)
        for selection_line in dictionary.values():
            self.accept_from_widget(json.dumps(selection_line))


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
        model: SelectionModel,
        parent,
        *args,
        **kwargs,
    ):
        """Create the selection dialog.

        Parameters
        ----------
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.
        model : SelectionModel
            Data object storing selection operations, shared with the main widget
        parent : QObject
            parent object in the Qt object hierarchy
        *args : Any, ...
            catches all the arguments that may be passed to the QDialog constructor
        **kwargs : dict[str, Any]
            catches all the keyword arguments passed to the QDialog constructor

        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self.setWindowFlags(Qt.Window)

        self.trajectory = traj_data[1]
        self.system = self.trajectory.chemical_system
        self.selection_model = model
        self.atm_full_names = self.system.name_list
        self.molecule_names = self.system.unique_molecules()
        self.labels = list(map(str, self.system._labels))

        self._trajectory_path = Path(self.trajectory.filename).parent
        self.selection_textbox = QPlainTextEdit()
        self.selection_textbox.setReadOnly(True)

        mol_view = MolecularViewerWithPicking()
        mol_view.clicked_atom_index.connect(self.update_from_3d_view)
        mol_view.picked_atoms_changed.connect(self.update_picked_atom_count)
        self.view_3d = View3D(mol_view)
        self.view_3d.update_panel(traj_data)

        layouts = self.create_layouts()

        self.bottom_buttons = QHBoxLayout()
        for button in self.create_buttons():
            self.bottom_buttons.addWidget(button)

        helper_layout = QHBoxLayout()
        sub_layout = QVBoxLayout()
        helper_layout.addLayout(layouts[0])
        helper_layout.addLayout(sub_layout)
        for layout in layouts[1:]:
            sub_layout.addLayout(layout)
        sub_layout.addLayout(self.bottom_buttons)

        self.setLayout(helper_layout)

        self.all_selection = True
        self.selected = set()
        self.reset()

    def closeEvent(self, a0):
        """Hide the window instead of closing.

        Some issues occur in the
        3D viewer when it is closed and then reopened.
        """
        self.selection_model.finalise_manual_selection()
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
        reset = QPushButton("Reset SELECTION")
        close = QPushButton("Close")
        reset.clicked.connect(self.reset)
        close.clicked.connect(self.close)
        return [reset, close]

    def create_optional_save_button(self):
        """Add a 'save selection' button.

        This is optional, because selection saving is available only in the
        AtomSelectionWidget, and not in the child classes for atom transmutation
        or setting partial charges.
        """
        button = QPushButton("Save selection", self)
        button.clicked.connect(self.save_selection_dialog)
        self.bottom_buttons.addWidget(button)

    def save_selection_dialog(self) -> None:
        """Load a selection from a file.

        At the moment it is possible to use .mda files which contain a selection,
        or JSON text files.
        """
        self.selection_model.finalise_manual_selection()
        fname = QFileDialog.getSaveFileName(
            self,
            "Save current selection to a JSON file",
            str(self._trajectory_path),
            "MDANSE selection files (*.json);;All files(*.*)",
        )
        if fname[0]:
            self.selection_model._selection.save_to_json_file(fname[0])

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
            GUISelection(self),
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
            if isinstance(widget, GUISelection):
                widget.confirm_gui_selection.clicked.connect(
                    self.selection_model.finalise_manual_selection,
                )
                widget.undo_gui_selection.clicked.connect(self.undo_manual_selection)
            else:
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
    def undo_manual_selection(self):
        """Remove all atoms (de)selected in the most recent manual selection."""
        self.selection_model.clear_manual_selection()
        self.recalculate_selection()

    @Slot()
    def recalculate_selection(self):
        """Update atom indices after selection change."""
        self.selected = self.selection_model.current_selection()
        self.view_3d._viewer.change_picked(self.selected)
        self.update_selection_textbox()

    @Slot(int)
    def update_from_3d_view(self, index: int) -> None:
        """Update atom indices after an atom has been clicked.

        A selection/deselection was made in the 3d view, update the
        check_boxes, combo_boxes and textbox.

        Parameters
        ----------
        index : int
            index of a single atom selected by clicking in View3D

        """
        self.selection_model.on_atom_clicked(index)
        self.update_selection_textbox()

    @Slot(object)
    def update_picked_atom_count(self, molview_selection: set[int]) -> None:
        """Use the number of selected atoms from 3D view to update the text box.

        Only used for manual selection of atoms.

        Parameters
        ----------
        molview_selection : set[int]
            set of all the selected atom indices, as provided by MolecularViewer

        """
        self.update_selection_textbox(len(molview_selection))

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

    def update_selection_textbox(self, num_atoms_3dview: int | None = None) -> None:
        """Update the textbox with the current atom selection information.

        Parameters
        ----------
        num_atoms_3dview : int | None, optional
            Number of atoms currently selected in 3D view, by default None

        """
        num_sel = num_atoms_3dview if num_atoms_3dview else len(self.selected)
        text = [f"Number of atoms selected:\n{num_sel}\n\nSelected atoms:\n"]
        for idx in self.selected:
            text.append(f"{idx}  ({self.atm_full_names[idx]})\n")
        self.selection_textbox.setPlainText("".join(text))

    def reset(self) -> None:
        """Reset the helper to the default state."""
        self.selection_model.clear()
        self.selection_model.accept_from_widget(
            '{"function_name": "select_all", "operation_type": "union"}'
        )
        self.selection_model.accept_from_widget(
            '{"function_name": "select_dummy", "operation_type": "difference"}'
        )
        self.recalculate_selection()


class AtomSelectionWidget(WidgetBase):
    """The atoms selection widget."""

    _push_button_text = "Atom selection helper"
    _load_button_text = "Load selection from file"
    _default_value = "{}"
    _tooltip_text = (
        "Specify which atoms will be used in the analysis. "
        "The input is a JSON string, and can be created"
        " using the helper dialog."
    )

    def __init__(self, *args, use_list_view: bool = True, **kwargs):
        """Create the main widget for atom selection."""
        super().__init__(*args, **kwargs)
        self._value = self._default_value
        if use_list_view:
            self._field = QListView(self._base)
            load_button = QPushButton(self._load_button_text, self._base)
            load_button.clicked.connect(self.load_selection_from_file_dialog)
        else:
            self._field = QLineEdit(self._base)
            default_text = str(self._configurator.default)
            self._field.setPlaceholderText(default_text)
            self._field.setText(default_text)
            self._field.setMaxLength(2147483647)
        traj_config = self._configurator.configurable[
            self._configurator.dependencies["trajectory"]
        ]
        traj_filename = traj_config["filename"]
        trajectory = traj_config["instance"]
        self._trajectory_path = Path(traj_filename).parent
        self.selection_model = SelectionModel(trajectory)
        self.selection_model.clear()
        self.selection_model.accept_from_widget(
            '{"function_name": "select_all", "operation_type": "union"}'
        )
        self.selection_model.accept_from_widget(
            '{"function_name": "select_dummy", "operation_type": "difference"}'
        )
        if use_list_view:
            self._field.setModel(self.selection_model)
        self.helper = None
        self.helper_settings = (traj_filename, trajectory)
        self.helper_save_button = False
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        if use_list_view:
            self._layout.addWidget(load_button)
            self.helper_save_button = True
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(self._tooltip_text)
        self.selection_model.selection_changed.connect(self.updateValue)

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
        return SelectionHelper(traj_data, self.selection_model, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Open the helper dialog."""
        if self.helper is None:
            self.helper = self.create_helper(self.helper_settings)
            if self.helper_save_button:
                self.helper.create_optional_save_button()
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
        else:
            if hasattr(self.helper, "previous_geometry"):
                self.helper.restoreGeometry(self.helper.previous_geometry)
            self.helper.show()

    @Slot()
    def load_selection_from_file_dialog(self) -> None:
        """Load a selection from a file.

        At the moment it is possible to use .mda files,
        or JSON text files.
        """
        fname = QFileDialog.getOpenFileName(
            self._base,
            "Load selection from a file (JSON or MDA)",
            str(self._trajectory_path),
            "MDANSE selection files (*.mda *.json);;HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)",
        )[0]
        if not fname:
            return
        temp_selection = ReusableSelection()
        try:
            temp_selection.load_from_hdf5(fname)
        except OSError:
            LOG.info("File %s could not be read as an HDF5 file", fname)
            try:
                temp_selection.load_from_json_file(fname)
            except (json.JSONDecodeError, UnicodeDecodeError):
                LOG.info("File %s could not be read using JSON decoder", fname)
                LOG.warning("Selection will NOT be loaded from %s", fname)
                return
        if not temp_selection.operations:
            LOG.warning("Selection from %s was empty and will be ignored", fname)
            return
        new_selection = temp_selection.convert_to_json()
        self.helper.selection_model.create_from_string(new_selection)

    def get_widget_value(self) -> str:
        """Return the current text in the input field.

        Returns
        -------
        str
            The JSON selector setting.

        """
        return self.selection_model.current_steps()
