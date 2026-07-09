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

import os

from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    PredictionSettings,
)
from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator

MAX_MEMORY_PER_PROCESS = int(os.environ.get("MDANSE_MAX_RAM_PER_PROCESS", "512"))


@IConfigurator.register("MemoryConfigurator")
class MemoryConfigurator(IntegerConfigurator):
    """Specified the upper limit of memory used by a single process.

    MDANSE will adjust the number of atoms or frames processed in a single
    analysis step to lower the memory requirements. However, this will not
    always be possible, as for large trajectories the memory limit may
    be exceeded already for a single atom or a single frame.
    """

    _default = MAX_MEMORY_PER_PROCESS

    choices = None

    label = "Memory options"
    tooltip = (
        "Set the upper limit of memory per process (MB) that you want MDANSE to use."
    )

    def __init__(self, name, **kwargs):
        self.memory_function = kwargs.pop("mem_function", None)
        super().__init__(name, **kwargs)
        self.prediction = PredictionSettings(
            key="memory_per_process", label="RAM per process (MB)"
        )
        self["memory_per_process"] = [1]

    def find_group_size(self) -> int:
        return 5

    def configure(self, value):
        """
        Configure the memory limit in MB.
        """
        if not self.update_needed(value):
            return

        self._original_input = value
        self.error_status = "OK"
        self.warning_status = ""

        try:
            num_value = int(value)
        except (TypeError, ValueError):
            self.error_status = (
                f"Input {num_value} cannot be converted to a number of MB."
            )
            return

        if num_value <= 0:
            self.error_status = (
                f"Upper limit of {num_value} MB cannot be used. Use a positive number."
            )
            return

        if self.memory_function is not None:
            predicted_memory = self.memory_function(self)
            self["memory_per_atom"] = predicted_memory[0] / 2**20
            self["memory_per_chunk"] = predicted_memory[1] / 2**20
            self["memory_per_step"] = (
                num_value // predicted_memory[0]
            ) * predicted_memory[0]
            if self["memory_per_step"] > num_value:
                self.warning_status = (
                    f"Expected memory per step ({self['memory_per_step']} MB) "
                    f"is larger than the requested upper limit ({num_value} MB)."
                )
            self["memory_per_process"] = [self["memory_per_step"]]

        self["value"] = num_value
        self.error_status = "OK"
