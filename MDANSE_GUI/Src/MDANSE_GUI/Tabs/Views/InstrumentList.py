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

import copy
import os

import tomlkit
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QStandardItem
from qtpy.QtWidgets import QAbstractItemView, QListView, QMenu
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import (
    InstrumentDetails,
    SimpleInstrument,
)


class InstrumentList(QListView):
    item_details = Signal(object)
    item_name = Signal(str)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)
        self._current_instrument = None
        self._all_instruments = set()
        self._backup_instruments = {}

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if index.row() == -1:
            # block right click when it's not on a trajectory
            return
        model = self.model()
        item = model.itemData(index)
        menu = QMenu()
        self.populateMenu(menu, item)
        menu.exec_(event.globalPos())

    def populateMenu(self, menu: QMenu, item: QStandardItem):
        has_backup = False
        instrument = self.model()._nodes[item[257]]
        if instrument is None:
            return
        if instrument._name in self._backup_instruments.keys():
            has_backup = True
        for action, method in [
            ("Delete instrument", self.deleteNode),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            if has_backup:
                temp_action.setEnabled(False)
        for action, method in [
            ("Duplicate instrument", self.duplicateNode),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
        for action, method in [
            ("Restore original parameters", self.restoreNode),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            if not has_backup:
                temp_action.setEnabled(False)

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        model.removeRow(index.row())
        self.item_details.emit(None)

    @Slot()
    def duplicateNode(self):
        model = self.model()
        index = self.currentIndex()
        node_number = model.itemFromIndex(index).data()
        instrument = model._nodes[node_number]
        new_instrument_name = instrument._name + " (Copy)"
        new_instrument = self.add_instrument(new_instrument_name)
        for line in new_instrument.inputs():
            attr_name = line[0]
            setattr(new_instrument, attr_name, getattr(instrument, attr_name, None))
        new_instrument._name = instrument._name + " (Copy)"
        if new_instrument._list_item is not None:
            new_instrument._list_item.setText(new_instrument_name)

    @Slot()
    def restoreNode(self):
        model = self.model()
        index = self.currentIndex()
        node_number = model.itemFromIndex(index).data()
        instrument = model._nodes[node_number]
        name = instrument._name
        # TBC
        try:
            backup = self._backup_instruments[name]
        except KeyError:
            LOG.error(f"Backup instrument not found: {name}")
        else:
            for line in instrument.inputs():
                attr_name = line[0]
                setattr(instrument, attr_name, getattr(backup, attr_name, None))
            self.item_details.emit(instrument)

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data()
        instrument = model._nodes[node_number]
        self._current_instrument = instrument
        self.item_details.emit(instrument)

    @Slot()
    def resend_item(self):
        self.item_details.emit(self._current_instrument)

    def add_instrument(self, optional_name=None) -> SimpleInstrument:
        model = self.model()
        if model is None:
            return
        new_instrument = SimpleInstrument()
        LOG.debug(f"New instrument, name: {new_instrument._name}")
        if optional_name is None:
            new_name = new_instrument._name
        else:
            new_name = optional_name
        model.append_object_and_embed((new_instrument, new_name))
        self._all_instruments.add(new_name)
        new_instrument.update_item()
        return new_instrument

    def connect_to_visualiser(self, visualiser: InstrumentDetails) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : View3D or TrajectoryInfo
            A visualiser to connect to this view.
        """
        try:
            self.item_details.connect(visualiser.update_panel)
        except Exception as e:
            LOG.error(f"Failed to connect InstrumentList to visualiser: {e}")

    def introduce_empty_instrument(self):
        self.model().append_object((None, "No instrument (default settings)"))

    def load_from_file(self, filename: str, keep_backups=False):
        source_file = TOMLFile(filename)
        try:
            tomldoc = source_file.read()
        except ParseError:
            LOG.error(f"File {filename} could not be parsed - TOML error")
            return
        for key in tomldoc.keys():
            if key in self._all_instruments:
                LOG.warning(
                    f"{key} already on instrument list. Overwriting from {filename}"
                )
                for node in self.model()._nodes.values():
                    new_instrument = node
                    if new_instrument is None:
                        continue
                    if new_instrument._name == key:
                        break
            else:
                new_instrument = self.add_instrument(str(key))
            if new_instrument is None:
                return
            if keep_backups:
                backup_instrument = SimpleInstrument()
            instrument_params = tomldoc[key]
            for input in SimpleInstrument.inputs():
                param_key = input[0]
                try:
                    new_value = instrument_params[param_key]
                except KeyError:
                    continue
                else:
                    setattr(new_instrument, param_key, new_value)
                    if keep_backups:
                        setattr(backup_instrument, param_key, new_value)
            if keep_backups:
                self._backup_instruments[str(key)] = backup_instrument
                new_instrument._name_is_fixed = True

    @Slot()
    def save_to_file(self, filename: str = None):
        if filename is None:
            filename = os.path.join(
                PLATFORM.application_directory(), "InstrumentDefinitions.toml"
            )
        LOG.debug(f"save to file: {filename}")
        target_file = TOMLFile(filename)
        newdoc = tomlkit.document()
        model = self.model()
        for instrument in model._nodes.values():
            if instrument is None:
                continue
            table = tomlkit.table()
            for input in SimpleInstrument.inputs():
                param_key = input[0]
                table[param_key] = getattr(instrument, param_key, "")
            newdoc[instrument._name] = table
        target_file.write(newdoc)
