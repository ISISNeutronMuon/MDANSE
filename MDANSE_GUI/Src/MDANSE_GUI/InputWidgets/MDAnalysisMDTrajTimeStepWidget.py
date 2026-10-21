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

from typing import TYPE_CHECKING

from MDANSE.Framework.Configurators import MDAnalysisTimeStepConfigurator

from .FloatWidget import FloatWidget

if TYPE_CHECKING:
    from MDANSE_GUI.InputWidgets import (
        MDAnalysisCoordinateFileWidget,
        MDAnalysisTopologyFileWidget,
    )


class MDAnalysisMDTrajTimeStepWidget(FloatWidget[MDAnalysisTimeStepConfigurator]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._last = None
        # file input widgets should be loaded into the _widgets list
        # before this one
        if widget := self.get_dep("topology_file"):
            self._topology_file_widget: MDAnalysisTopologyFileWidget = widget
            self._topology_file_widget.value_changed.connect(self.update_from_files)
        if widget := self.get_dep("coordinate_files"):
            self._coordinates_file_widget: MDAnalysisCoordinateFileWidget = widget
            self._coordinates_file_widget.value_changed.connect(self.update_from_files)

    def update_from_files(self) -> None:
        """Updates the time step field from the topology and coordinates
        files if possible else set it back to the default value.
        """
        if (
            current := (
                self._topology_file_widget._field.text(),
                self._coordinates_file_widget._field.text(),
            )
        ) == self._last:
            return

        self._configurator.configure(None)
        if self._configurator.valid:
            self._field.setText(str(self._configurator["value"]))
        else:
            self._field.setText(str(self._default_value))
        self._last = current
