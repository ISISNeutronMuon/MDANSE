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
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
    QWidget,
)

from MDANSE.Framework.Configurators.AtomTransmutationConfigurator import AtomTransmuter
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import SelectionHelper


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
        traj_data: tuple[str, HDFTrajectoryInputData],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """
        Parameters
        ----------
        transmuter : AtomTransmuter
            The MDANSE atom transmuter initialized with the current
            chemical system.
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        self.transmuter = transmuter
        self.transmutation_textbox = QTextEdit()
        self.transmutation_textbox.setReadOnly(True)
        self.transmutation_combo = QComboBox()
        self.transmutation_combo.addItems(ATOMS_DATABASE.atoms)
        self.transmuter.selector.settings["all"] = False
        super().__init__(
            transmuter.selector,
            traj_data,
            field,
            parent,
            *args,
            **kwargs,
        )
        self.all_selection = False
        self.update_transmutation_textbox()

    def right_widgets(self) -> list[QWidget]:
        widgets = super().right_widgets()
        return widgets + [self.transmutation_textbox]

    def left_widgets(self) -> list[QWidget]:
        """Adds a transmutation widget to the selection helper.

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
        return widgets + [transmutation]

    def apply_transmutation(self) -> None:
        """With the selection and the transmutation choice apply the
        transmutation and update the transmutation textbox with the new
        transmutation setting.
        """
        self.transmuter.apply_transmutation(
            self.full_settings, self.transmutation_combo.currentText()
        )
        self.update_transmutation_textbox()

    def update_transmutation_textbox(self) -> None:
        """Update the transmutation textbox with the current transmuter
        setting information.
        """
        map = self.transmuter.get_setting()

        text = [f"Number of atoms transmuted:\n{len(map)}\n\nTransmuted atoms:\n"]
        atoms = self.selector.system.atom_list
        for idx, symbol in map.items():
            text.append(
                f"{idx}  ({atoms[idx].full_name}): {atoms[idx].symbol} -> {symbol}\n"
            )

        self.transmutation_textbox.setText("".join(text))

    def reset(self):
        """Reset the transmuter so that no transmutation are set."""
        super().reset()
        self.transmuter.reset_setting()
        self.update_transmutation_textbox()

    def apply(self) -> None:
        """Set the field of the AtomTransmutationWidget to the currently
        chosen setting in this widget.
        """
        self._field.setText(self.transmuter.get_json_setting())


class AtomTransmutationWidget(AtomSelectionWidget):
    """The atoms transmutation widget."""

    _push_button_text = "Atom transmutation helper"
    _default_value = "{}"
    _tooltip_text = "Specify the atom transmutation that will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."

    def create_helper(
        self, traj_data: tuple[str, HDFTrajectoryInputData]
    ) -> TransmutationHelper:
        """
        Parameters
        ----------
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        TransmutationHelper
            Create and return the transmutation helper QDialog.
        """
        transmuter = self._configurator.get_transmuter()
        return TransmutationHelper(transmuter, traj_data, self._field, self._base)
