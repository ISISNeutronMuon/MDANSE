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

import tempfile
import time
from pathlib import Path
from typing import Any

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


def parse_dictionary(input: str) -> dict[str, Any]:
    big_line = input.strip("{}[] \n")
    tokens = big_line.split(",")
    result = {}
    for entry in tokens:
        temp = entry.split(":")
        key, value = temp[0], ":".join(temp[1:])
        key = key.strip("' ")
        value = value.strip(" '")
        try:
            value = int(value)
        except Exception:
            try:
                value = float(value)
            except Exception:
                pass
        result[key] = value
    return result


class McStasOptionsConfigurator(IConfigurator):
    """
    This configurator allows to input the McStas options that will be used to run a McStas executable file.
    """

    _default = {
        "ncount": 10000,
        "dir": (
            Path(tempfile.gettempdir())
            / "mcstas_output"
            / time.strftime("%d.%m.%Y-%H:%M:%S", time.localtime())
        ),
    }

    def configure(self, value):
        """
        Configure the McStas options.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the McStas options.
        :type value: dict
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        options = self._default.copy()

        parsed = parse_dictionary(value)

        for k, v in list(parsed.items()):
            if k not in options:
                continue
            options[k] = v

        tmp = [""]
        for k, v in list(options.items()):
            if k == "dir":
                # If the output directory already exists, defines a 'unique' output directory name because otherwise McStas throws.
                if Path(v).exists():
                    v = self._default["dir"]  # noqa: PLW2901
                self["mcstas_output_directory"] = Path(v)
            tmp.append(f"--{k}={v}")

        dirname = self["mcstas_output_directory"].parent

        try:
            PLATFORM.create_directory(dirname)
        except Exception:
            self.error_status = f"The directory {dirname} is not writable"
            return

        self["value"] = tmp
        self.error_status = "OK"
