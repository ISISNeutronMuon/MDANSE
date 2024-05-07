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
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
    QWidget,
)
from qtpy.QtGui import QDoubleValidator

from MDANSE.Framework.Configurators.PartialChargeConfigurator import PartialChargeMapper
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import SelectionHelper


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
        traj_data: tuple[str, HDFTrajectoryInputData],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """
        Parameters
        ----------
        mapper : PartialChargeMapper
            The charge mapper initialized with the current chemical
            system.
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        self.mapper = mapper
        self.charge_textbox = QTextEdit()
        self.charge_textbox.setReadOnly(True)
        self.charge_qline = QLineEdit()
        self.charge_qline.setValidator(QDoubleValidator())
        self.mapper.selector.settings["all"] = False
        super().__init__(
            mapper.selector, traj_data, field, parent, min_width=750, *args, **kwargs
        )
        self.update_charge_textbox()

    def create_buttons(self) -> list[QPushButton]:
        """
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
        """Add one addition layout to the right over the selection
        helper.

        Returns
        -------
        list[QVBoxLayout]
            List of QVBoxLayout to add to the helper layout.
        """
        layouts = super().create_layouts()
        right = QVBoxLayout()
        right.addWidget(self.charge_textbox)
        return layouts + [right]

    def left_widgets(self) -> list[QWidget]:
        """Adds a partial charge widget to the selection helper.

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
        return widgets + [partial_charge]

    def apply_charges(self) -> None:
        """With the selection and the charge choice update the charge
        mapper and update the charge textbox with the new partial
        charge map info.
        """
        try:
            charge = float(self.charge_qline.text())
        except ValueError:
            # probably an empty QLineEdit box
            return
        self.mapper.update_charges(self.full_settings, charge)
        self.update_charge_textbox()

    def update_charge_textbox(self) -> None:
        """Update the partial charge textbox with the current charge
        mapper setting information.
        """
        map = self.mapper.get_full_setting()

        text = [f"Partial charge mapping:\n"]
        atoms = self.selector.system.atom_list
        for idx, charge in map.items():
            text.append(f"{idx}  ({atoms[idx].full_name}) -> {charge}\n")

        self.charge_textbox.setText("".join(text))

    def reset(self):
        """Reset the mapper so that no charges are set."""
        self.mapper.reset_setting()
        self.update_charge_textbox()

    def apply(self) -> None:
        """Set the field of the PartialChargeWidget to the currently
        chosen setting in this widget.
        """
        self._field.setText(self.mapper.get_json_setting())


class PartialChargeWidget(AtomSelectionWidget):
    """The partial charge widget."""

    _push_button_text = "Partial charge helper"
    _default_value = "{}"
    _tooltip_text = "Specify the partial charges that will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."

    def create_helper(
        self, traj_data: tuple[str, HDFTrajectoryInputData]
    ) -> ChargeHelper:
        """
        Parameters
        ----------
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        ChargeHelper
            Create and return the partial charge helper QDialog.
        """
        mapper = self._configurator.get_charge_mapper()
        return ChargeHelper(mapper, traj_data, self._field, self._base)
