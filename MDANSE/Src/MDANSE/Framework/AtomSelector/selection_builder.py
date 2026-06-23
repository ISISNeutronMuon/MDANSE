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
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.IO.IOUtils import json_handler

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class OperationType(Enum):
    """OperationType Enum for standardisation of names."""

    SET = auto()
    UNION = auto()
    INTERSECTION = auto()
    DIFFERENCE = auto()

    OR = UNION
    AND = INTERSECTION
    DIFF = DIFFERENCE

    @classmethod
    def _missing_(cls, value: str):
        if not isinstance(value, str):
            return None
        return vars(cls).get(value.upper())


class SelectionBuilder:
    """Helper class to build selections via the python interface.

    Parameters
    ----------
    basis : dict | str | Path, optional
        Starting point to build Selection builder on in json format.
    """

    def __init__(self, basis: dict | str | Path | None = None):
        self.ops = self.load(basis) if basis else []

    def __getitem__(self, key: int | slice) -> tuple[str, dict[str, Any]]:
        new = type(self)()
        if isinstance(key, int):
            new.ops = [self.ops[key]]
        else:
            new.ops = self.ops[key]
        return new

    def __delitem__(self, key: int) -> None:
        del self.ops[key]

    def copy(self):
        """Return a disconnected copy."""
        return SelectionBuilder(self.as_json)

    def reorder(self, new_order: Iterable[int]):
        """Reorder ops.

        Items will be in the new order. Any missing items will be dropped.

        Parameters
        ----------
        new_order : Iterable[int]
            Dictionary of new order of operations.

        """
        self.ops = [self[ind] for ind in new_order]
        return self

    def load(self, source: dict | str | Path):
        """Load a selection builder from a dump.

        Parameters
        ----------
        source : dict | str | Path
            Source json file or string or dict to use.

        """
        value = json_handler(source)
        for _, val in sorted(value.items(), key=lambda x: x[0]):
            params = val.copy()
            self.ops.append(params.pop("function_name"), params)

    @property
    def as_selection(self) -> ReusableSelection:
        """Return a ReusableSelection with this configuration.

        Returns
        -------
        ReusableSelection
            Usable ReusableSelection object.

        """
        sel = ReusableSelection()
        sel.load(self.as_dict)
        return sel

    @property
    def as_dict(self) -> dict[int, dict[str, Any]]:
        """Return a dictionary suitable for loading with a ReusableSelection.

        Returns
        -------
        dict[int, dict[str, Any]]
            Builder as dict.

        """
        return {
            idx: {"function_name": key} | params
            for idx, (key, params) in enumerate(self.ops)
        }

    @property
    def as_json(self) -> str:
        """Return JSON str of this object.

        Returns
        -------
        str
            JSONised selection.

        """
        return json.dumps(self.as_dict)

    def apply(self, trajectory: Trajectory) -> set[int]:
        """Apply this selection and see which indices would be returned.

        Parameters
        ----------
        trajectory : Trajectory
            Trajectory to try selection on.

        Returns
        -------
        set[int]
            Indices which would be selected.

        """
        return self.as_selection.select_in_trajectory(trajectory)

    @staticmethod
    def _filter_nop(args: dict[str, Any]) -> dict[str, Any]:
        """Helper function to remove falsey values from a dict.

        Parameters
        ----------
        args : dict[str, Any]
            Dict to sanitise.

        Returns
        -------
        dict[str, Any]
            Dict with false values removed.

        """
        return {key: val for key, val in args.items() if val}

    def select_all(self) -> None:
        """Select all the atoms in the trajectory."""
        self.ops.append(("select_all", {}))
        return self

    def select_none(self) -> None:
        """Set an empty selection."""
        self.ops.append(("select_none", {}))
        return self

    def invert_selection(self) -> None:
        """Invert the current selection for the input trajectory.

        Return a set of all the indices that are present in the trajectory
        and were not included in the input selection.
        """
        self.ops.append(("invert_selection", {}))
        return self

    def select_atoms(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        index_list: Sequence[int] | None = None,
        index_range: Sequence[int] | None = None,
        index_slice: Sequence[int] | None = None,
        atom_types: Sequence[str] = (),
        atom_names: Sequence[str] = (),
    ) -> None:
        """Select specific atoms in the trajectory.

        Atoms can be selected based
        on indices, atom type or trajectory-specific atom name.
        The atom type is normally the chemical element, while
        the atom name can be more specific and depend on the
        force field used.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        index_list : Sequence[int]
            A list of indices to be selected.
        index_range : Sequence[int]
            A pair of (first, last+1) indices defining a range.
        index_slice : Sequence[int]
            A sequence of (first, last+1, step) indices defining a slice.
        atom_types : Sequence[str]
            A list of atom types (i.e. chemical elements) to be selected, given as string.
        atom_names : Sequence[str]
            A list of atom names (as used by the MD engine, force field, etc.) to be selected.
        """
        operation_type = OperationType(operation_type).name.lower()
        kwargs = self._filter_nop(
            {
                "index_list": index_list,
                "index_range": index_range,
                "index_slice": index_slice,
                "atom_types": atom_types,
                "atom_names": atom_names,
            }
        )

        self.ops.append(("select_atoms", kwargs | {"operation_type": operation_type}))
        return self

    def select_dummy(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
    ) -> None:
        """Select all atoms with the dummy property.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        """
        operation_type = OperationType(operation_type).name.lower()
        self.ops.append(("select_dummy", {"operation_type": operation_type}))

    def select_molecules(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        molecule_names: Sequence[str],
    ) -> None:
        """Selects all the atoms belonging to the specified molecule types.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        molecule_names : Sequence[str]
            a list of molecule names (str) which are keys of ChemicalSystem._clusters
        """
        operation_type = OperationType(operation_type).name.lower()
        self.ops.append(
            (
                "select_molecules",
                {
                    "operation_type": operation_type,
                    "molecule_names": molecule_names,
                },
            )
        )
        return self

    def select_labels(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        atom_labels: Sequence[str],
    ) -> None:
        """Select atoms with a specific label in the trajectory.

        A residue name can be used as a label by MDANSE.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        atom_labels : Sequence[str]
            a list of string labels (e.g. residue names) by which to select atoms
        """
        operation_type = OperationType(operation_type).name.lower()
        self.ops.append(
            (
                "select_labels",
                {
                    "operation_type": operation_type,
                    "atom_labels": atom_labels,
                },
            )
        )
        return self

    def select_pattern(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        rdkit_pattern: str,
    ) -> None:
        """Select atoms according to the SMARTS string given as input.

        This will only work if molecules and bonds have been detected in the system.
        If the bond information was not read from the input trajectory on conversion,
        it can still be determined in a TrajectoryEditor run.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        rdkit_pattern : str
            a SMARTS string to be matched
        """
        operation_type = OperationType(operation_type).name.lower()
        self.ops.append(
            (
                "select_pattern",
                {
                    "operation_type": operation_type,
                    "rdkit_pattern": rdkit_pattern,
                },
            )
        )
        return self

    def select_positions(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        frame_number: int = 0,
        position_minimum: Sequence[float] | None = None,
        position_maximum: Sequence[float] | None = None,
    ) -> None:
        """Select atoms based on their positions at a specified frame number.

        Lower and upper limits of x, y and z coordinates can be given as input.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        frame_number : int, optional
            trajectory frame at which to check the coordinates, by default 0
        position_minimum : Sequence[float], optional
            (x, y, z) lower limits of coordinates to be selected, by default None
        position_maximum : Sequence[float], optional
            (x, y, z) upper limits of coordinates to be selected, by default None
        """
        operation_type = OperationType(operation_type).name.lower()
        kwargs = {
            "frame_number": frame_number,
            "position_minimum": position_minimum,
            "position_maximum": position_maximum,
        }
        self.ops.append(
            ("select_positions", kwargs | {"operation_type": operation_type})
        )
        return self

    def select_sphere(
        self,
        *,
        operation_type: OperationType = OperationType.UNION,
        frame_number: int = 0,
        sphere_centre: tuple[float, float, float],
        sphere_radius: float,
    ) -> None:
        """Select atoms within a sphere.

        Selects atoms at a given distance from a fixed point in space,
        based on coordinates at a specific frame number.

        Parameters
        ----------
        operation_type: OperationType
            What set operation to perform.
        frame_number : int, optional
            trajectory frame at which to check the coordinates, by default 0
        sphere_centre : Sequence[float]
            (x, y, z) coordinates of the centre of the selection
        sphere_radius : float
            distance from the centre within which to select atoms
        """
        operation_type = OperationType(operation_type).name.lower()
        kwargs = {
            "frame_number": frame_number,
            "sphere_centre": sphere_centre,
            "sphere_radius": sphere_radius,
        }
        self.ops.append(("select_sphere", kwargs | {"operation_type": operation_type}))
        return self

    def save(self, filename: Path | str):
        """Output all the operations as a JSON string.

        For the purpose of storing the selection independent of the
        trajectory it is acting on, this method encodes the sequence
        of selection operations as a string.

        Returns
        -------
        str
            All the operations of this selection, encoded as string

        """
        with open(filename, "w") as target:
            json.dump(self.as_dict, target, indent=2)

    def __str__(self) -> str:
        if not self.ops:
            return f"{type(self).__name__}()"
        return (
            f"{type(self).__name__}(\n"
            + "\n".join(
                f"    {ind}: {op}(...)," for ind, (op, _) in enumerate(self.ops)
            )
            + "\n)"
        )

    def __repr__(self) -> str:
        if not self.ops:
            return f"{type(self).__name__}()"
        return (
            f"{type(self).__name__}(\n"
            + "\n".join(
                f"    {ind}: {op}("
                + ", ".join(f"{key}={val!r}" for key, val in params.items())
                + ")"
                for ind, (op, params) in enumerate(self.ops)
            )
            + "\n)"
        )
