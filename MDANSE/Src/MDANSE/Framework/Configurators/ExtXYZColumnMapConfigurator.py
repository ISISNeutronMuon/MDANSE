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
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, NamedTuple, NotRequired, Self, TypedDict

from more_itertools import first, first_true
from typing_extensions import override

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Units import UnitError, _Unit, measure
from MDANSE.MLogging import LOG
from MDANSE.util_types import FloatArray

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators import MultiFileWithAtomDataConfigurator
    from MDANSE.Framework.Parsers.extxyz import ExtXYZFile


class Reference(NamedTuple):
    key: str
    file: str
    info: bool = False

    def __str__(self) -> str:
        return f"{self.key}:{self.file}"

    @classmethod
    def from_str(cls, value: str, info: bool = False) -> Self:
        col, fn = value.split(":", maxsplit=1)
        return cls(col, fn, info)


@IConfigurator.register("ExtXYZColumnMapConfigurator")
class ExtXYZColumnMapConfigurator(IConfigurator):
    """The Extxyz column mapping configurator for trajectory converters."""

    ARRAY_ALIASES = {
        "species": ("spec", "atom", "atoms", "species"),
        "positions": ("psn", "pos", "positions", "crd", "coords", "coordinates"),
        "velocities": ("vel", "velo", "velocity", "velocities"),
        "momenta": ("momenta", "moment", "momentum"),
        "masses": ("mas", "mass", "masses"),
        "forces": ("frc", "grd", "force", "forces", "gradients", "grad"),
        "time": ("time",),
        "unit_cell": ("unit_cell", "cell", "box", "pbox"),
    }
    UNIT_DEFAULTS = {
        "species": measure(1.0, "unitless"),
        "positions": measure(1.0, "ang"),
        "velocities": measure(1.0, "ang / ps"),
        "momenta": measure(1.0, "Da ang / ps"),
        "masses": measure(1.0, "Da"),
        "forces": measure(1.0, "Da ang / ps2"),
        "time": measure(1.0, "ps"),
        "unit_cell": measure(1.0, "ang"),
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
        self.mapping: dict[str, Reference | None] = {}
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
            Reference(key, Path(file).name, info=False): val
            for file, parser in parsers.items()
            for key, val in parser.arrays.items()
        }
        infos = {
            Reference(key, Path(file).name, info=True): val
            for file, parser in parsers.items()
            for key, val in parser.info.items()
        }
        self.columns = list(arrays) + list(infos)

        if not value:
            self.mapping = self.get_default_mapping(infos, arrays)
            self.units = self.get_default_units(infos)
            return
        else:
            isinfo = {*map(str, infos)}
            self.mapping = {
                key: Reference.from_str(val[0], info=str(val[0]) in isinfo)
                if val[0] is not None
                else None
                for key, val in value.items()
            }
            self.units = {key: val[1] for key, val in value.items()}

        if mismatch := set(self.mapping.values()) - {
            *self.columns,
            "None",
            None,
        }:
            raise ValueError(
                f"Keys mismatched between provided dict and file ({mismatch})."
            )

    def get_default_mapping(
        self, infos: dict[Reference, Any], arrays: dict[Reference, FloatArray]
    ) -> dict[str, Reference | None]:

        def find_array_key(keys: Iterable[Reference], *trial: str) -> Reference | None:
            if key := first(
                (key for key in keys for elem in trial if elem in key.file),
                default=None,
            ):  # Filename contains property
                return key

            return first(
                (key for key in keys for elem in trial if elem in key.key),
                default=None,
            )  # Key in property

        mapping = dict.fromkeys(self.ARRAY_ALIASES, None)

        all_keys = arrays.keys() | infos.keys()

        for name, keys in self.ARRAY_ALIASES.items():
            if key := find_array_key(all_keys, *keys):
                mapping[name] = key
            else:
                LOG.info("Cannot determine %s key.", name)

        return mapping

    @staticmethod
    def _de_alias(key: str) -> str:
        return first(
            (
                mdkey
                for mdkey, aliases in ExtXYZColumnMapConfigurator.ARRAY_ALIASES.items()
                if key in aliases
            ),
            default=key,
        )

    def _process_units(self, key: str, val: str) -> dict[str, _Unit]:
        if key == "units":
            val = val.removeprefix("_JSON").strip()

            if not val.startswith("{"):
                raise ValueError(f"Unable to process units from {val}.")

            ud = json.loads(val)
            if not isinstance(ud, dict):
                raise ValueError("Units doesn't appear to be JSON dict.")

            units = {}
            for ukey, unit in ud.items():
                unit_clean = unit.replace("^", "").replace("Ang", "ang")
                try:
                    units[self._de_alias(ukey)] = measure(1.0, unit_clean)
                except UnitError:
                    LOG.warning(f"Unable to parse unit {unit}")
            return units

        if key.startswith("units_"):
            try:
                return {self._de_alias(key.removeprefix("units_")): measure(1.0, val)}
            except UnitError:
                LOG.warning(f"Unable to parse unit {val}")

        raise ValueError(f"Don't know how to handle {val}")

    def get_default_units(self, infos: dict[Reference, Any]) -> dict[str, str]:
        """Get units associated with values.

        Tries to take them from the extxyz file, failing that return defaults.

        Parameters
        ----------
        infos : dict[Reference, Any]
            Info arrays.

        Returns
        -------
        dict[str, str]
            Mapping of units to valid unit string.
        """

        if not any("units" in key.key for key in infos):
            return {key: val._uname for key, val in self.UNIT_DEFAULTS.items()}

        unit_info = {
            Reference(typ, key.file, info=True): unit
            for key in infos
            if "units" in key.key
            for typ, unit in self._process_units(key.key, infos[key]).items()
        }

        out_units = {}

        for key, val in self.mapping.items():
            if val in {None, "None"}:
                out_units[key] = self.UNIT_DEFAULTS[key]._uname
                continue

            out_units[key] = unit_info.get(
                val._replace(info=True), self.UNIT_DEFAULTS[key]
            )._uname

        return out_units
