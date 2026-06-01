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

from pathlib import Path
from typing import TYPE_CHECKING, Any

import h5py
from typing_extensions import TypeVar

from MDANSE.Framework.Parameters.Parameters import (
    SENTINEL,
    ConfigError,
    Configurable,
    ConfigureDescriptor,
)
from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory
from MDANSE.MolecularDynamics.Trajectory import Trajectory

if TYPE_CHECKING:
    from .UtilTypes import Depends


def set_up_trajectory(self, trajectory: Trajectory, deps):
    """Apply operations to the trajectory instance, if present.

    Atom selection, atom transmutation and result grouping are all
    applied to the Trajectory object. If the job works on a trajectory,
    the Trajectory instance is now saved as an attribute of this IJob
    instance.

    These operations were previously handled by IConfigurator subclasses.
    """
    if (selection := deps.get("selection")) is not None:
        trajectory.set_selection(selection)
    if (transmutation := deps.get("transmutation")) is not None:
        trajectory.set_transmutation(transmutation)
    if (grouping := deps.get("grouping")) is not None:
        trajectory.set_grouping(grouping)

    return trajectory


MT = TypeVar("MT", default=Trajectory)


class MDANSETrajectory(ConfigureDescriptor[str | Path, Trajectory, MT]):
    default_tooltip = "Input MDANSE trajectory from converter or h5md file."
    default_label = "Trajectory to use."

    def __init__(
        self,
        *,
        selection: str | None = None,
        transmutation: str | None = None,
        grouping: str | None = None,
        requires_cell: bool = False,
        **params,
    ):
        super().__init__(**params)

        self.requires_cell = requires_cell
        self._special_deps = {
            key: val
            for key, val in [
                ("selection", selection),
                ("transmutation", transmutation),
                ("grouping", grouping),
            ]
            if val is not None
        }

        self.extension = {
            "MDANSE trajectory": "mdt",
            "HDF5 file": "h5",
            "All files": "*",
        }

    def __get__(self, owner: Configurable, obj_type) -> MT:
        out = super().__get__(owner, obj_type)

        deps = {}
        for key, val in self._special_deps.items():
            desc = owner.descriptors[val]
            value = getattr(owner, desc.private_name, SENTINEL)
            if value is SENTINEL:
                value = desc.validate(desc.default, {"trajectory": out})
            deps[key] = value

        return set_up_trajectory(self, out, deps)

    def __set__(
        self, owner: Configurable, value: Path | str | Trajectory | MockTrajectory
    ):
        if isinstance(value, (Trajectory, MockTrajectory)):
            setattr(owner, self.private_name, value)
            setattr(owner, self.configured_var, True)
            setattr(owner, self.raw_name, value.filename)
            self._validate_dependents(owner)
            return

        super().__set__(owner, value)

    def _validate_choices(
        self,
        value: Trajectory,
        choices: set[str] | None = None,
    ) -> bool:
        choice_in = self.choices if choices is None else choices
        return all(value.has_variable(choice) for choice in choice_in)

    def _validate_exclude(
        self,
        value: Trajectory,
        exclude: set[str] | None = None,
    ) -> bool:
        exclude_in = self.exclude if exclude is None else exclude
        return not any(value.has_variable(exclude) for exclude in exclude_in)

    def validate(self, value, deps: Depends) -> Trajectory:
        try:
            value = Path(value).expanduser()
        except TypeError as error:
            raise ConfigError(f"Value ({value}) is not a valid Path.") from error

        if not value.exists():
            raise ConfigError(f"File at ({value}) does not exist.")

        try:
            out = Trajectory(value)
        except Exception:
            raise ConfigError(f"Could not load file ({value}) as Trajectory") from None

        out = super().validate(out, deps)

        return out


MR = TypeVar("MR", default=h5py.File)


class MDANSEResult(ConfigureDescriptor[str | Path | h5py.File, h5py.File, MR]):
    default_tooltip = "Input MDANSE result from prior analysis."

    def __init__(
        self,
        **params,
    ):
        super().__init__(**params)
        self.extension = {
            "MDANSE result": "*.mda",
            "HDF5 file": "*.h5",
            "All files": "*",
        }

    def _validate_choices(
        self,
        value: h5py.File,
        choices: set[str] | None = None,
    ) -> bool:
        choice_in = self.choices if choices is None else choices
        return all(choice in value for choice in choice_in)

    def _validate_exclude(
        self,
        value: h5py.File,
        exclude: set[str] | None = None,
    ) -> bool:
        excludes = self.exclude if exclude is None else exclude
        return not any(exclude in value for exclude in excludes)

    def validate(self, value, deps: dict[str, Any]) -> h5py.File | None:
        if self.optional and value is None:
            return None

        try:
            value = Path(value).expanduser()
        except TypeError as error:
            raise ConfigError(f"Value ({value}) is not a valid Path.") from error

        if not value.exists():
            raise ConfigError(f"{value} does not exist.")

        try:
            out = h5py.File(value)
        except Exception:
            raise ConfigError(f"Could not load file ({value}) as hdf5.") from None

        if not self._validate_choices(out):
            missing = {str(choice) for choice in self.choices if choice not in out}
            raise ConfigError(f"Missing keys ({', '.join(missing)}) in {out.filename}.")

        if not self._validate_exclude(out):
            extra = {str(excl) for excl in self.exclude if excl not in out}
            raise ConfigError(
                f"Extraneous keys ({', '.join(extra)}) in {out.filename}."
            )

        return out
