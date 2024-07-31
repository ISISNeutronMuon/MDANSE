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
import os
import tomlkit
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from qtpy.QtCore import Slot, Signal, QModelIndex, Qt
from qtpy.QtWidgets import QListView, QAbstractItemView

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

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        model.removeRow(index.row())
        self.item_details.emit(("", None))

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

    def load_from_file(self, filename: str):
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
                    if new_instrument._name == key:
                        break
            else:
                new_instrument = self.add_instrument(str(key))
            if new_instrument is None:
                return
            instrument_params = tomldoc[key]
            for input in SimpleInstrument.inputs():
                param_key = input[0]
                try:
                    new_value = instrument_params[param_key]
                except KeyError:
                    continue
                else:
                    setattr(new_instrument, param_key, new_value)

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
            table = tomlkit.table()
            for input in SimpleInstrument.inputs():
                param_key = input[0]
                table[param_key] = getattr(instrument, param_key, "")
            newdoc[instrument._name] = table
        target_file.write(newdoc)
