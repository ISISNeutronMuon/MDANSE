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

import json
from typing import TYPE_CHECKING, Any

from more_itertools import first_true
from qtpy.QtGui import QStandardItemModel
from typing_extensions import override

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators import FileWithAtomDataConfigurator
    from MDANSE.Framework.Parsers.extxyz import ExtXYZFile


@IConfigurator.register("ExtXYZColumnMapConfigurator")
class ExtXYZColumnMapConfigurator(IConfigurator):
    """The Extxyz column mapping configurator for trajectory converters."""

    KEY_DEFAULTS = {
        "positions": ("pos", "positions", "coords", "coordinates"),
        "velocities": ("velo", "velocity", "velocities"),
        "momenta": ("momenta", "moment", "momentum"),
        "masses": ("mass", "masses"),
        "forces": ("force", "forces", "gradients", "grad"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}

    @override
    def configure(self, value: dict[str, str | None] | None = None) -> None:
        """
        Parameters
        ----------
        value : str
            The atom map setting JSON string.
        """

        file_configurator: FileWithAtomDataConfigurator[ExtXYZFile] = self.configurable[
            self.dependencies["input_file"]
        ]
        if not file_configurator.valid:
            self.error_status = "Input file not selected or valid."
            return

        parser = file_configurator.parser_instance
        assert parser is not None

        _info, arrays = parser.columns
        self.columns = arrays.keys()
        if not value:
            self.mapping = self.get_default_mapping(arrays)
        elif mismatch := set(value.values()) - {*self.columns, "None", None}:
            raise ValueError(f"Keys mismatched between provided dict and file ({mismatch}).")
        else:
            self.mapping = value

    def get_default_mapping(self, arrays: dict[str, Any]) -> dict[str, str | None]:
        def find_array_key(*trial: str) -> str | None:
            return first_true(trial, pred=arrays.__contains__, default=None)

        mapping = dict.fromkeys(self.KEY_DEFAULTS, "None")
        for name, keys in self.KEY_DEFAULTS.items():
            if key := find_array_key(*keys):
                mapping[name] = key
            else:
                LOG.info("Cannot determine %s key.", name)

        return mapping
