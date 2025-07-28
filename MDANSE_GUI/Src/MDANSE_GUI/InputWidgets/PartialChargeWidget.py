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

from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.Configurators.PartialChargeConfigurator import PartialChargeMapper
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import (
    AtomSelectionWidget,
    SelectionHelper,
    SelectionModel,
)


class ChargeHelper(SelectionHelper):
    """Generates a string that specifies the partial charge mapping.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.

    """

    _helper_title = "Partial charge helper"

    def __init__(
        self,
        mapper: PartialChargeMapper,
        traj_data: tuple[str, Trajectory],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """Build a helper dialog for setting atom charges.

        Parameters
        ----------
        mapper : PartialChargeMapper
            The charge mapper initialized with the current chemical
            system.
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        parent : QObject
            Parent object in the Qt hierarchy of objects
        *args : Any, ...
            catches all the arguments that may be passed to the QDialog constructor
        **kwargs : dict[str, Any]
            catches all the keyword arguments passed to the QDialog constructor

        """
        self.mapper = mapper
        self.charge_textbox = QTextEdit()
        self.charge_textbox.setReadOnly(True)
        self.charge_qline = QLineEdit()
        self.charge_qline.setValidator(QDoubleValidator())
        self.inner_model = SelectionModel(traj_data[1])
        self._field = field
        super().__init__(traj_data, self.inner_model, parent, *args, **kwargs)
        charge_reset = QPushButton("Reset CHARGES", self)
        charge_reset.clicked.connect(self.reset_charges)
        self.bottom_buttons.addWidget(charge_reset)
        self.all_selection = False
        self.update_charge_textbox()

    def right_widgets(self) -> list[QWidget]:
        """Add the charge textbox to the right widgets.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the right layout from
            create_layouts.

        """
        widgets = super().right_widgets()
        return [*widgets, self.charge_textbox]

    def left_widgets(self) -> list[QWidget]:
        """Add a partial charge widget to the selection helper.

        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the first layout from
            create_layouts.

        """
        widgets = super().left_widgets()
        partial_charge = QGroupBox("partial_charge")
        charge_layout = QVBoxLayout()

        combo_layout = QHBoxLayout()
        label = QLabel("Set charge of selection to:")

        combo_layout.addWidget(label)
        combo_layout.addWidget(self.charge_qline)
        charge_layout.addLayout(combo_layout)

        apply_charge = QPushButton("Apply")
        charge_layout.addWidget(apply_charge)
        apply_charge.clicked.connect(self.apply_charges)

        partial_charge.setLayout(charge_layout)
        return [*widgets, partial_charge]

    def apply_charges(self) -> None:
        """Set charges of the curretly selected atoms."""
        try:
            charge = float(self.charge_qline.text())
        except ValueError:
            # probably an empty QLineEdit box
            return
        self.selection_model.finalise_manual_selection()
        selection_string = self.selection_model.current_steps()
        self.mapper.update_charges(selection_string, charge)
        self.update_charge_textbox()
        self.apply()

    def update_charge_textbox(self) -> None:
        """Show the current atom charges in the text box."""
        charge_map = self.mapper.get_full_setting()

        text = ["Partial charge mapping:\n"]
        for idx, charge in charge_map.items():
            text.append(f"{idx}  ({self.atm_full_names[idx]}) -> {charge}\n")

        self.charge_textbox.setText("".join(text))

    def reset_charges(self):
        """Reset the mapper so that no charges are set."""
        self.mapper.reset_setting()
        self.update_charge_textbox()
        self.apply()

    def apply(self) -> None:
        """Pass the charge setting to the main widget."""
        self._field.setText(self.mapper.get_json_setting())


class PartialChargeWidget(AtomSelectionWidget):
    """The partial charge widget."""

    _push_button_text = "Partial charge helper"
    _default_value = "{}"
    _tooltip_text = (
        "Specify the partial charges that will be used in the analysis."
        " The input is a JSON string, and can be created using"
        " the helper dialog."
    )

    def __init__(self, *args, **kwargs):
        """Create the widget for setting atom charges.

        Parameters
        ----------
        _use_list_view : bool, optional
            ignored here. This widget always sets use_list_view=False

        """
        if kwargs.get("use_list_view", False):
            raise TypeError(f"Cannot use list view with {type(self).__name__}.")
        super().__init__(*args, use_list_view=False, **kwargs)
        self._field.textChanged.connect(self.updateValue)

    def create_helper(self, traj_data: tuple[str, Trajectory]) -> ChargeHelper:
        """Create the dialog for selecting atoms and setting their charges.

        Parameters
        ----------
        traj_data : tuple[str, Trajectory]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        ChargeHelper
            Create and return the partial charge helper QDialog.

        """
        mapper = self._configurator.get_charge_mapper()
        return ChargeHelper(mapper, traj_data, self._field, self._base)

    def get_widget_value(self) -> str:
        """Return the current text in the input field.

        Returns
        -------
        str
            The JSON selector setting.

        """
        text = self._field.text()
        return text if text else self._default_value
