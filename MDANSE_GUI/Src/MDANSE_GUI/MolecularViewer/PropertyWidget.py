#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

from collections import ChainMap
from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QComboBox, QTableView, QVBoxLayout, QWidget

from MDANSE.Chemistry import ATOMS_DATABASE

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class Const:
    """Dummy namespace for ``match`` syntax."""

    def __init__(self, value):
        self.v = value


class _Update(Enum):
    """Scheme for update based on datatypes"""

    NO_UPDATE = auto()
    UNIT_CELL = auto()
    TRAJECTORY_ATOM_PROP = auto()
    TRAJECTORY_ATOM_VEC = auto()
    RAW_ATOM_PROP = auto()
    RAW_SYSTEM_PROP = auto()

    ATOM_DATA = NO_UPDATE
    RAW_CONSTANT_ATOM_PROP = NO_UPDATE
    RAW_CONSTANT_SYSTEM_PROP = NO_UPDATE


class PropertyWidget(QWidget):
    """Widget to inspect trajectory properties."""

    def __init__(self, parent: QWidget, index: int | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.viewer = self.parent()
        self._last_prop = None
        self._populate_layout()
        self._index = index
        self.active = False
        self.viewer.frame_changed.connect(self.update_table)
        self._atom_props = {}
        self._raw_props = {}
        self._frame_props = {}
        self._trajectory_props = {}
        self.curr_selection = {}

    @Slot(int)
    def _active(self, index: int):
        self.active = index == self._index
        if self.active:
            self.update_table()

    @Slot()
    def _activate(self):
        self.active = True

    @Slot()
    def _deactivate(self):
        self.active = False

    def _populate_layout(self) -> None:
        """Initialise layout.

        Creates all the widgets, places them in the layout and
        connects their signals and slots.
        """
        layout = self.layout()

        self._prop_type = QComboBox(self)
        self._prop_type.setEditable(False)
        self._prop_type.addItems(["atoms", "trajectory"])
        self._prop_type.setCurrentIndex(0)
        self._prop_type.currentTextChanged.connect(self.get_props)
        self._prop_type.currentTextChanged.connect(self._activate)

        self._prop_selection = QComboBox(self)
        self._prop_selection.setEditable(False)
        self._prop_selection.currentTextChanged.connect(self.update_table)
        self._prop_selection.currentTextChanged.connect(self._activate)

        self._prop_model = QStandardItemModel()
        self._prop_table = QTableView(self)
        self._prop_table.setModel(self._prop_model)
        self._prop_table.setTextElideMode(Qt.ElideNone)

        layout.addWidget(self._prop_type)
        layout.addWidget(self._prop_selection)
        layout.addWidget(self._prop_table)

    def _extract_atom_prop(self, atom_prop: str) -> list:
        """Get per-atom properties in system.

        Parameters
        ----------
        atom_prop : str
            Propert to retrieve.

        Returns
        -------
        list
            List of properties per-atom.
        """
        return [
            self._trajectory.get_atom_property(symbol, atom_prop)
            for symbol in self._trajectory.atom_names
        ]

    def extract_props(self, trajectory: Trajectory) -> None:
        """Determine properties in system and create lazy getters.

        Parameters
        ----------
        trajectory : Trajectory
            Trajectory to process.
        """
        self._prop_selection.clear()
        self._trajectory = trajectory
        self._atom_props: dict[str, Callable[[], Sequence]] = {
            **{
                property_name: partial(self._extract_atom_prop, property_name)
                for property_name in trajectory.properties
            },
        }

        self._raw_props: dict[str, Callable[[], Sequence]] = {
            f"raw_{property_name}": partial(trajectory.variable, property_name)
            for property_name in trajectory.variables()
        }
        self._frame_props: dict[str, Callable[[int], Sequence]] = {
            prop: getattr(trajectory, prop)
            for prop in ("charges", "coordinates", "unit_cell")
        }

        self._trajectory_props = ChainMap(self._frame_props, self._raw_props)

        self.get_props()

    @Slot()
    def get_props(self) -> None:
        """Get the available properties for a given class of properties."""
        self._prop_selection.clear()

        match self._prop_type.currentText():
            case "atoms":
                self.curr_selection = self._atom_props
            case "trajectory":
                self.curr_selection = self._trajectory_props

        self._last_prop = None

        self._prop_selection.addItems(sorted(filter(None, self.curr_selection)))

    @staticmethod
    def _make_items(*items: Any) -> list[QStandardItem]:
        """Build :class:`QStandardItem` s from arguments.

        Parameters
        ----------
        *items : Any
            Items to add

        Returns
        -------
        list[QStandardItem]
            List of ``items`` as :class:`QStandardItem`
        """

        items = [QStandardItem(str(item)) for item in items]
        for item in items:
            item.setEditable(False)
        return items

    def _set_horiz_labels(self, *items: str) -> None:
        """Set horizontal labels

        Parameters
        ----------
        *items : Any
            Labels to use.
        """
        for i, label in enumerate(items):
            idx = QStandardItem(str(label))
            self._prop_model.setHorizontalHeaderItem(i, idx)

    def _set_vert_labels(self, *items) -> None:
        """Set vertical labels.

        Parameters
        ----------
        *items : str
            Labels to use, if not specified atom-indices are used.
        """
        if not items:
            items = range(self.viewer._n_atoms)

        for i, label in enumerate(items):
            idx = QStandardItem(str(label))
            self._prop_model.setVerticalHeaderItem(i, idx)

    def _construct_prop_table(self, prop_type: str, prop_name: str) -> None:
        """Build property table.

        This may be a long operation, the :meth:`_update_prop_table` should be faster
        in principle.

        Parameters
        ----------
        prop_type : str
            Property type to extract.
        prop_name : str
            Name of property within prop_type.
        """

        self._prop_model.clear()
        frame = self.viewer._current_frame
        data = (
            self.curr_selection[prop_name](frame)
            if prop_name in self._frame_props
            else self.curr_selection[prop_name]()
        )

        match prop_type, prop_name:
            case ("atoms", name):
                self.update = _Update.ATOM_DATA

                for atom_name, prop in zip(
                    self._trajectory.atom_names,
                    data,
                    strict=True,
                ):
                    items = self._make_items(atom_name, prop)
                    self._prop_model.appendRow(items)

                header = (
                    name
                    if (unit := self._trajectory.units.get(prop_name, "none")) == "none"
                    else f"{name} ({unit})"
                )
                self._set_horiz_labels("name", header)
                self._set_vert_labels()

            case ("trajectory", "charges"):
                self.update = _Update.TRAJECTORY_ATOM_PROP

                for atom_name, prop in zip(
                    self._trajectory.atom_names,
                    data,
                    strict=True,
                ):
                    items = self._make_items(atom_name, prop)
                    self._prop_model.appendRow(items)

                self._set_horiz_labels("name", "charge")
                self._set_vert_labels()

            case ("trajectory", "coordinates"):
                self.update = _Update.TRAJECTORY_ATOM_VEC

                for atom_name, prop in zip(
                    self._trajectory.atom_names,
                    data,
                    strict=True,
                ):
                    items = self._make_items(atom_name, *prop)
                    self._prop_model.appendRow(items)

                self._set_horiz_labels("name", "x", "y", "z")
                self._set_vert_labels()

            case ("trajectory", "unit_cell"):
                self.update = _Update.UNIT_CELL
                if not data:
                    items = self._make_items("No unit cell")
                    self._prop_model.appendRow(items)
                    return

                for prop in data.direct:
                    items = self._make_items(*prop)
                    self._prop_model.appendRow(items)

                self._set_horiz_labels("x", "y", "z")
                self._set_vert_labels("a", "b", "c")

            case ("trajectory", _):
                n_frames = Const(self.viewer._n_frames)
                n_atoms = Const(self.viewer._n_atoms)

                match data.shape:
                    case (n_frames.v, n_atoms.v, *_):
                        self.update = _Update.RAW_ATOM_PROP

                        for atom_name, prop in zip(
                            self._trajectory.atom_names,
                            data[frame, :, ...],
                            strict=True,
                        ):
                            items = self._make_items(atom_name, *prop)
                            self._prop_model.appendRow(items)

                    case (n_atoms.v, *_):
                        self.update = _Update.RAW_CONSTANT_ATOM_PROP

                        for atom_name, prop in zip(
                            self._trajectory.atom_names,
                            data,
                            strict=True,
                        ):
                            items = self._make_items(atom_name, prop)
                            self._prop_model.appendRow(items)

                    case (n_frames.v, *_):
                        self.update = _Update.RAW_SYSTEM_PROP

                        for prop in data[frame, ...]:
                            items = self._make_items(*prop)
                            self._prop_model.appendRow(items)

                    case _:
                        self.update = _Update.RAW_CONSTANT_SYSTEM_PROP

                        for prop in data:
                            items = self._make_items(*prop)
                            self._prop_model.appendRow(items)

                self._set_horiz_labels(*range(self._prop_model.columnCount()))
                self._set_vert_labels(*range(self._prop_model.rowCount()))

            case _:
                self.update = _Update.NO_UPDATE

        self._prop_table.resizeColumnsToContents()

    def _update_prop_table(self, prop_name: str) -> None:
        """Update values in existing table.

        Parameters
        ----------
        prop_name : str
            Name of data to extract.

        Raises
        ------
        NotImplementedError
            Unrecognised update type.
        """
        if self.update == _Update.NO_UPDATE:
            return

        frame = self.viewer._current_frame
        data = (
            self.curr_selection[prop_name](frame)
            if prop_name in self._frame_props
            else self.curr_selection[prop_name]()
        )

        match self.update:
            case _Update.UNIT_CELL:
                if not data:
                    return

                for i, row in enumerate(data.direct):
                    for j, elem in enumerate(row):
                        self._prop_model.item(i, j).setText(str(elem))
            case _Update.TRAJECTORY_ATOM_PROP:
                for i, elem in enumerate(data):
                    self._prop_model.item(i, 1).setText(str(elem))

            case _Update.RAW_ATOM_PROP:
                for i, row in enumerate(data[frame, :, ...]):
                    for j, elem in enumerate(row, 1):
                        self._prop_model.item(i, j).setText(str(elem))

            case _Update.TRAJECTORY_ATOM_VEC:
                for i, row in enumerate(data):
                    for j, elem in enumerate(row, 1):
                        self._prop_model.item(i, j).setText(str(elem))

            case _Update.RAW_SYSTEM_PROP:
                for i, row in enumerate(data[frame, ...]):
                    for j, elem in enumerate(row):
                        self._prop_model.item(i, j).setText(str(elem))

            case _:
                raise NotImplementedError(
                    f"Prop {prop_name} has unrecognised update-schema {self.update}."
                )

    @Slot()
    def update_table(self) -> None:
        """Update table with data.

        In case of property changing, reconstruct existing table otherwise
        update values.
        """
        if not self.active:
            return

        prop_name = self._prop_selection.currentText()
        prop_type = self._prop_type.currentText()

        if not prop_name:
            return

        prop_change = prop_name != self._last_prop

        if prop_change:
            self._construct_prop_table(prop_type, prop_name)
        else:
            self._update_prop_table(prop_name)

        self._last_prop = prop_name

    def clear_viewer(self):
        """Clears the property viewer."""
        self._prop_selection.clear()
        self._prop_model.clear()
        self._atom_props.clear()
        self._raw_props.clear()
        self._frame_props.clear()
        self._trajectory_props.clear()
        self.curr_selection.clear()
