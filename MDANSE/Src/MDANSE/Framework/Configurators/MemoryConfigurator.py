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

from MDANSE.Core.Settings import Option, Settings
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    PredictionSettings,
)
from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator


@Settings.parametrise(
    memory_warning_limit=Option(
        1024,
        group="memory",
        comment="Amount of RAM per process (MB) which will trigger a warning in the GUI.",
    ),
)
@IConfigurator.register("MemoryConfigurator")
class MemoryConfigurator(IntegerConfigurator):
    """Number of atoms processed at the same time.

    This input will try to calculate the predicted memory requirements
    of the analysis based on the other input parameters. Each analysis
    type provides its own memory calculation function, which has to be
    calibrated.
    """

    _default = 256

    choices = None

    label = "Atoms per step (performance option)"
    tooltip = "Set the number of atoms to process per step and check the predicted memory needs."

    def __init__(self, name, **kwargs):
        self.memory_function = kwargs.pop("mem_function", None)
        super().__init__(name, **kwargs)
        self.prediction_list = [
            PredictionSettings(
                key="memory_per_process", label="RAM per process", unit="MB"
            ),
            PredictionSettings(
                key="atoms_per_step",
                label="Atoms processed in a single step",
            ),
        ]
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
                f"Input {num_value} cannot be converted to a number of atoms."
            )
            return

        if num_value <= 0:
            self.error_status = f"Number of atoms per step has to be positive. Current value is {num_value}."
            return

        atoms_per_chunk = self.configurable[self.dependencies["trajectory"]][
            "instance"
        ].chunk_size(array_name="position")

        if self.memory_function is not None:
            predicted_memory = self.memory_function(self)
            self["memory_per_atom"] = predicted_memory[0]
            self["memory_per_chunk"] = predicted_memory[1]
            atoms_per_step = min(num_value, atoms_per_chunk)
            self["memory_per_step"] = atoms_per_step * predicted_memory[0]
            self["atoms_per_step"] = [atoms_per_step]
            if self["memory_per_step"] > self.memory_warning_limit:
                self.warning_status = (
                    f"Expected memory per step ({self['memory_per_step']} MB) "
                    f"is larger than the current preferred limit ({self.memory_warning_limit} MB)."
                )
            self["memory_per_process"] = [self["memory_per_step"]]
        else:
            self.warning_status = (
                "There is no valid function for memory use calculations"
            )
            self["atoms_per_step"] = [1]
            self["memory_per_step"] = [-1]

        self["value"] = num_value
        self.error_status = "OK"
