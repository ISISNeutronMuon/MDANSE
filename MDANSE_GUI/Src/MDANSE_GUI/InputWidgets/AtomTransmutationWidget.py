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

from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.AtomTransmutationConfigurator import AtomTransmuter
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import (
    AtomSelectionWidget,
    SelectionHelper,
    SelectionModel,
)


class TransmutationHelper(SelectionHelper):
    """Generates a string that specifies the atom transmutation.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.

    """

    _helper_title = "Atom transmutation helper"

    def __init__(
        self,
        transmuter: AtomTransmuter,
        traj_data: tuple[str, Trajectory],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """Create a dialog for atom transmutation.

        Parameters
        ----------
        transmuter : AtomTransmuter
            The MDANSE atom transmuter initialized with the current
            chemical system.
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        parent : QObject
            parent object in the Qt object hierarchy
        *args : Any, ...
            catches all the arguments that may be passed to the QDialog constructor
        **kwargs : dict[str, Any]
            catches all the keyword arguments passed to the QDialog constructor

        """
        self.transmuter = transmuter
        self.transmutation_textbox = QTextEdit()
        self.transmutation_textbox.setReadOnly(True)
        self.transmutation_combo = QComboBox()
        self.transmutation_combo.addItems(ATOMS_DATABASE.atoms)
        self._field = field
        self.inner_model = SelectionModel(traj_data[1])
        super().__init__(
            traj_data,
            self.inner_model,
            parent,
            *args,
            **kwargs,
        )
        transmutation_reset = QPushButton("Reset TRANSMUTATION", self)
        transmutation_reset.clicked.connect(self.reset_transmuation)
        self.bottom_buttons.addWidget(transmutation_reset)
        self.update_transmutation_textbox()

    def right_widgets(self) -> list[QWidget]:
        """Add the transmutation textbox to the right widgets.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the right layout from
            create_layouts.

        """
        widgets = super().right_widgets()
        return [*widgets, self.transmutation_textbox]

    def left_widgets(self) -> list[QWidget]:
        """Add a transmutation widget to the selection helper.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the first layout from
            create_layouts.

        """
        widgets = super().left_widgets()
        transmutation = QGroupBox("transmutation")
        transmutation_layout = QVBoxLayout()

        combo_layout = QHBoxLayout()
        label = QLabel("Transmute selection to:")

        combo_layout.addWidget(label)
        combo_layout.addWidget(self.transmutation_combo)
        transmutation_layout.addLayout(combo_layout)

        transmute = QPushButton("Transmute")
        transmutation_layout.addWidget(transmute)
        transmute.clicked.connect(self.apply_transmutation)

        transmutation.setLayout(transmutation_layout)
        return [*widgets, transmutation]

    def apply_transmutation(self) -> None:
        """Apply the transmutation to the selected atoms."""
        self.inner_model.finalise_manual_selection()
        selection_string = self.selection_model.current_steps()
        self.transmuter.apply_transmutation(
            selection_string,
            self.transmutation_combo.currentText(),
        )
        self.update_transmutation_textbox()
        self.apply()

    def update_transmutation_textbox(self) -> None:
        """Update the list of transmuted atoms in the text box."""
        substitutions = self.transmuter.get_setting()

        text = [
            f"Number of atoms transmuted:\n{len(substitutions)}\n\nTransmuted atoms:\n",
        ]
        for idx, symbol in substitutions.items():
            text.append(f"{idx}  {self.atm_full_names[idx]} -> {symbol}\n")

        self.transmutation_textbox.setText("".join(text))

    def reset_transmuation(self):
        """Reset the transmuter so that no transmutation are set."""
        self.transmuter.reset_setting()
        self.update_transmutation_textbox()
        self.apply()

    def apply(self) -> None:
        """Pass the transmutation settings to the main widget."""
        self._field.setText(self.transmuter.get_json_setting())


class AtomTransmutationWidget(AtomSelectionWidget):
    """The atoms transmutation widget."""

    _push_button_text = "Atom transmutation helper"
    _default_value = "{}"
    _tooltip_text = (
        "Specify the atom transmutation that will be used in the analysis."
        " The input is a JSON string, and can be created using"
        " the helper dialog."
    )

    def __init__(self, *args, **kwargs):
        """Create the main widget for transmuting atom types.

        Parameters
        ----------
        _use_list_view : bool, optional
            If True, a ListView will replace LineEdit, by default True

        """
        if kwargs.get("use_list_view", False):
            raise TypeError(f"Cannot use list view with {type(self).__name__}.")
        super().__init__(*args, use_list_view=False, **kwargs)
        self._field.textChanged.connect(self.updateValue)

    def create_helper(self, traj_data: tuple[str, Trajectory]) -> TransmutationHelper:
        """Create a helper dialog for selecting and transmuting atoms.

        Parameters
        ----------
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        TransmutationHelper
            Create and return the transmutation helper QDialog.

        """
        transmuter = self._configurator.get_transmuter()
        return TransmutationHelper(transmuter, traj_data, self._field, self._base)

    def get_widget_value(self) -> str:
        """Return the current text in the input field.

        Returns
        -------
        str
            The JSON selector setting.

        """
        text = self._field.text()
        return text if text else self._default_value
