from __future__ import annotations

from collections import ChainMap
from collections.abc import Callable, Sequence
from functools import partial
from itertools import count

import h5py
from more_itertools import prepend
from qtpy.QtCore import Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QComboBox, QTableView, QVBoxLayout, QWidget

from MDANSE.MolecularDynamics.Trajectory import Trajectory


class PropertyWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.viewer = self.parent()
        self._last_prop = None
        self._populate_layout()
        self.viewer.frame_changed.connect(self.update_table)

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

        self._prop_selection = QComboBox(self)
        self._prop_selection.setEditable(False)
        self._prop_selection.currentTextChanged.connect(self.update_table)

        self._prop_model = QStandardItemModel()
        self._prop_table = QTableView(self)
        self._prop_table.setModel(self._prop_model)

        layout.addWidget(self._prop_type)
        layout.addWidget(self._prop_selection)
        layout.addWidget(self._prop_table)

    def _extract_atom_prop(self, atom_prop: str) -> list:
        return [
            self._trajectory.get_atom_property(symbol, atom_prop)
            for symbol in self._trajectory.atom_names
        ]

    def extract_props(self, trajectory: Trajectory) -> None:
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
    def get_props(self) -> NOne:
        self._prop_selection.clear()

        match self._prop_type.currentText():
            case "atoms":
                self.curr_selection = self._atom_props
            case "trajectory":
                self.curr_selection = self._trajectory_props

        self._last_prop = None
        self._prop_selection.addItems(self.curr_selection.keys())

    @staticmethod
    def _make_items(*items) -> list[QStandardItem]:
        items = [QStandardItem(str(item)) for item in items]
        for item in items:
            item.setEditable(False)
        return items

    def _set_horiz_labels(self, *items) -> None:
        for i, label in enumerate(items):
            idx = QStandardItem(str(label))
            self._prop_model.setHorizontalHeaderItem(i, idx)


    @Slot()
    def update_table(self) -> None:
        frame = self.viewer._current_frame
        prop_name = self._prop_selection.currentText()
        if not prop_name:
            self._prop_model.clear()
            return
        prop_change = prop_name != self._last_prop

        match self._prop_type.currentText():
            case "atoms" if prop_change:
                self._prop_model.clear()
                for (i, name), prop in zip(
                    enumerate(self._trajectory.atom_names),
                    self.curr_selection[prop_name](),
                    strict=True,
                ):
                    items = self._make_items(name, prop)
                    self._prop_model.appendRow(items)

                    idx = QStandardItem(str(i))
                    self._prop_model.setVerticalHeaderItem(i, idx)

                self._set_horiz_labels("name", prop_name)


            case "trajectory" if prop_name in self._frame_props:

                data = self.curr_selection[prop_name](frame)
                self._prop_model.clear()

                match prop_name:
                    case "charges":
                        for (i, name), prop in zip(
                            enumerate(self._trajectory.atom_names),
                            data,
                            strict=True,
                        ):
                            items = self._make_items(name, prop)
                            self._prop_model.appendRow(items)

                            idx = QStandardItem(str(i))
                            self._prop_model.setVerticalHeaderItem(i, idx)

                        self._set_horiz_labels("name", "charge")

                    case "coordinates":
                        for (i, name), prop in zip(
                            enumerate(self._trajectory.atom_names),
                            data,
                            strict=True,
                        ):
                            items = self._make_items(name, *prop)
                            self._prop_model.appendRow(items)

                            idx = QStandardItem(str(i))
                            self._prop_model.setVerticalHeaderItem(i, idx)

                        self._set_horiz_labels("name", "x", "y", "z")

                    case "unit_cell":
                        if not data:
                            items = self._make_items("No unit cell")
                            self._prop_model.appendRow(items)
                            return

                        for prop in data.direct:
                            items = self._make_items(*prop)
                            self._prop_model.appendRow(items)

                        for i, label in enumerate("xyz"):
                            idx = QStandardItem(label)
                            self._prop_model.setVerticalHeaderItem(i, idx)
                            idx = QStandardItem(label)
                            self._prop_model.setHorizontalHeaderItem(i, idx)

                self._prop_table.resizeColumnsToContents()

            case "trajectory":
                data = self.curr_selection[prop_name]()
                if not isinstance(data, h5py.Dataset):
                    return

                match data.shape:
                    case (
                        self.viewer._n_frames,
                        self.viewer._n_atoms,
                        *_,
                    ):  # Atom property?
                        self._prop_model.clear()

                        for (i, name), prop in zip(
                            enumerate(self._trajectory.atom_names),
                            data[frame, :, ...],
                            strict=True,
                        ):
                            items = self._make_items(name, *prop)
                            self._prop_model.appendRow(items)

                            idx = QStandardItem(str(i))
                            self._prop_model.setVerticalHeaderItem(i, idx)

                    case self.viewer._n_atoms if prop_change:  # Constant atom property
                        self._prop_model.clear()

                        for (i, name), prop in zip(
                            enumerate(self._trajectory.atom_names),
                            data,
                            strict=True,
                        ):
                            items = self._make_items(name, prop)
                            self._prop_model.appendRow(items)

                            idx = QStandardItem(str(i))
                            self._prop_model.setVerticalHeaderItem(i, idx)

                    case (self.viewer._n_frames, *_):  # System property
                        self._prop_model.clear()

                        for prop in data[frame, ...]:
                            items = self._make_items(name, *prop)
                            self._prop_model.appendRow(items)

                    case _ if prop_change:  # Constant system property
                        self._prop_model.clear()

                        for prop in data:
                            items = self._make_items(*prop)
                            self._prop_model.appendRow(items)

                self._set_horiz_labels(*range(self._prop_model.columnCount()))

        self._last_prop = prop_name
