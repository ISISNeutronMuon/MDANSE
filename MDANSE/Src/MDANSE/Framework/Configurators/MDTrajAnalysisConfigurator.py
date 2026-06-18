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

from typing import Any

from mdtraj import baker_hubbard, wernet_nilsson

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.mdtraj.analysis import mdtraj_initial_params

MDTRAJ_JOBS = {
    "Hydrogen Bonds: Baker-Hubbard": baker_hubbard,
    "Hydrogen Bonds: Wernet-Nilsson": wernet_nilsson,
}


@IConfigurator.register("MDTrajAnalysisConfigurator")
class MDTrajAnalysisConfigurator(IConfigurator):
    """ """

    _default = (
        "Hydrogen Bonds: Baker-Hubbard",
        {},
    )
    label = "Analysis from MDTraj"
    tooltip = "Function and input parameters"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def configure(self, value: tuple[str, list[Any], dict[str, Any]]):
        """Create a vector generator with given parameters.

        Parameters
        ----------
        value : tuple[str, dict[str, Any]]
            Class name and dictionary of input parameters

        """
        if not self.update_needed(value):
            return

        self._original_input = value

        self.error_status = "OK"
        self.warning_status = ""
        try:
            if not isinstance(value, tuple):
                raise Exception(
                    f"MDTraj Analysis needs a (name, parameters) tuple. Got {value}"
                )

            try:
                function_name, arguments, keyword_parameters = value
            except ValueError as err:
                raise Exception(f"Invalid MDTraj Analysis settings {value}") from err

            if function_name not in MDTRAJ_JOBS:
                raise ValueError(
                    f"Analysis {function_name} is not implemented in MDANSE"
                )

            function = MDTRAJ_JOBS[function_name]
            args, kwargs = mdtraj_initial_params(function)
            args.remove("traj")

            unknown_keywords = set(keyword_parameters) - {item[0] for item in kwargs}
            if len(unknown_keywords):
                self.warning_status = f"Parameters {unknown_keywords} were given, but are not used by {function_name}"

            if len(args) != len(arguments):
                self.warning_status = (
                    f"Expected {len(args)} unnamed argument, but got {len(arguments)}"
                )

            self["args"] = arguments
            self["kwargs"] = keyword_parameters
            self["function"] = function_name

        except Exception as err:
            self.error_status = str(err)
            return

        self["value"] = value
        self.error_status = "OK"
