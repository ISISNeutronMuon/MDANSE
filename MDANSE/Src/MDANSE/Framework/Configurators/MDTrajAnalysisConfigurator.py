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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.mdtraj.analysis import mdtraj_initial_params


@IConfigurator.register("MDTrajAnalysisConfigurator")
class MDTrajAnalysisConfigurator(IConfigurator):
    """Chooses an analysis run implemented in MDTraj and sets its input parameters."""

    _default = (
        [],
        {},
    )
    label = "Analysis from MDTraj"
    tooltip = "Function and input parameters"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mdtraj_function = kwargs.get("mdtraj_function")
        args, kwargs = mdtraj_initial_params(mdtraj_function)
        args.remove("traj")
        self.mdtraj_function = mdtraj_function
        self.expected_args = args
        self.expected_kwargs = kwargs

    def configure(self, value: tuple[list[Any], dict[str, Any]]):
        """Create a vector generator with given parameters.

        Parameters
        ----------
        value : tuple[list[Any], dict[str, Any]]
            List of arguments and dictionary of keyword arguments with default values.

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
                arguments, keyword_parameters = value
            except ValueError as err:
                raise Exception(f"Invalid MDTraj Analysis settings {value}") from err

            unknown_keywords = set(keyword_parameters) - {
                item[0] for item in self.expected_kwargs
            }
            if len(unknown_keywords):
                self.warning_status = f"Parameters {unknown_keywords} were given, but are not used by {self.mdtraj_function}"

            if len(self.expected_args) != len(arguments):
                self.warning_status = f"Expected {len(self.expected_args)} unnamed arguments, but got {len(arguments)}"

            self["args"] = arguments
            self["kwargs"] = keyword_parameters

        except Exception as err:
            self.error_status = str(err)
            return

        self["value"] = value
        self.error_status = "OK"
