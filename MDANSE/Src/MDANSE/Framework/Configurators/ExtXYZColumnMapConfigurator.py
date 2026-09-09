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
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, NotRequired, Generic

from more_itertools import first, first_true
from qtpy.QtGui import QStandardItemModel
from typing_extensions import override

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators import MultiFileWithAtomDataConfigurator
    from MDANSE.Framework.Parsers.extxyz import ExtXYZFile


@IConfigurator.register("ExtXYZColumnMapConfigurator")
class ExtXYZColumnMapConfigurator(IConfigurator):
    """The Extxyz column mapping configurator for trajectory converters."""

    KEY_DEFAULTS = {
        "species": ("spec", "atom", "atoms", "species"),
        "positions": ("psn", "pos", "positions", "crd", "coords", "coordinates"),
        "velocities": ("vel", "velo", "velocity", "velocities"),
        "momenta": ("momenta", "moment", "momentum"),
        "masses": ("mas", "mass", "masses"),
        "forces": ("frc", "grd", "force", "forces", "gradients", "grad"),
    }

    class Mapping(TypedDict):
        species: str
        positions: str
        velocities: NotRequired[str]
        momenta: NotRequired[str]
        masses: NotRequired[str]
        forces: NotRequired[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}
        self.units = {}

    @override
    def configure(self, value: dict[str, str | None] | None = None) -> None:
        """
        Parameters
        ----------
        value : str
            The atom map setting JSON string.
        """

        file_configurator: MultiFileWithAtomDataConfigurator[ExtXYZFile] = (
            self.configurable[self.dependencies["input_file"]]
        )
        if not file_configurator.valid:
            self.error_status = "Input file not selected or valid."
            return

        parsers = file_configurator.parser_instances

        arrays = {
            f"{key}:{Path(file).name}": val
            for file, parser in parsers.items()
            for key, val in parser.arrays.items()
        }
        self.columns = list(arrays)

        if not value:
            self.mapping = self.get_default_mapping(arrays)
            self.units = dict.fromkeys(self.mapping, None)
        elif mismatch := {val for val, _unit in value.values()} - {*self.columns, "None", None}:
            raise ValueError(
                f"Keys mismatched between provided dict and file ({mismatch})."
            )
        else:
            self.mapping, self.units = zip(*value.values())

    @staticmethod
    def _partition(arrays: dict[str, Any]) -> dict[str, str]:
        return {key.split(":")[1]: key.split(":")[0] for key in arrays}

    def get_default_mapping(self, arrays: dict[str, Any]) -> dict[str, str | None]:
        maps = self._partition(arrays)

        def find_array_key(*trial: str) -> str | None:
            if key := first(
                (
                    f"{col}:{fn}"
                    for fn, col in maps.items()
                    for elem in trial
                    if elem in fn
                ),
                default=None,
            ):  # Filename contains property
                return key

            return first(
                (
                    f"{col}:{fn}"
                    for fn, col in maps.items()
                    for elem in trial
                    if elem in col
                ),
                default=None,
            )  # Key in property

        mapping = dict.fromkeys(self.KEY_DEFAULTS, "None")
        for name, keys in self.KEY_DEFAULTS.items():
            if key := find_array_key(*keys):
                mapping[name] = key
            else:
                LOG.info("Cannot determine %s key.", name)

        return mapping
