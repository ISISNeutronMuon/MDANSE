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
from pathlib import PurePath

import MDAnalysis as mda
from qtpy.QtWidgets import QFileDialog
from qtpy.QtCore import Slot

from MDANSE.MLogging import LOG
from .TopologyFileWidget import TopologyFileWidget


class CoordinateFileWidget(TopologyFileWidget):

    def __init__(self, *args, file_dialog=QFileDialog.getOpenFileNames, **kwargs):
        super().__init__(
            *args,
            file_dialog=file_dialog,
            format_options=sorted(mda._READERS.keys()),
            **kwargs,
        )
        for widget in self.parent()._widgets:
            if (
                widget._configurator
                is self._configurator._configurable[
                    self._configurator._dependencies["input_file"]
                ]
            ):
                widget.value_changed.connect(self.updateValue)

    @Slot()
    def valueFromDialog(self):
        paths_group = self._settings.group("paths")
        try:
            self.default_path = paths_group.get(self._job_name)
        except:
            LOG.warning(f"session.get_path failed for {self._job_name}")
        new_value = self._file_dialog(
            self.parent(),
            "Load file",
            str(self.default_path),
            self._qt_file_association,
        )

        if new_value is not None and new_value[0]:
            values = ['"' + str(PurePath(value)) + '"' for value in new_value[0]]
            self._field.setText("[" + ", ".join(values) + "]")
            self.updateValue()
            try:
                LOG.info(
                    f"Settings path of {self._job_name} to {os.path.split(new_value[0][0])[0]}"
                )
                paths_group.set(
                    self._job_name, str(PurePath(os.path.split(new_value[0][0])[0]))
                )
            except:
                LOG.error(
                    f"session.set_path failed for {self._job_name}, {os.path.split(new_value[0][0])[0]}"
                )
