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
from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeAlias

import numpy as np
import numpy.typing as npt
from more_itertools import bucket
from typing_extensions import TypeVar

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.AtomMapping import check_mapping_valid, fill_remaining_labels
from MDANSE.Framework.AtomSelector.selector import (
    ReusableSelection,
    SelectionOperations,
)
from MDANSE.Framework.Parameters.Choices import SingleChoice
from MDANSE.Framework.Parameters.Parameters import ConfigError, ConfigureDescriptor
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID
from MDANSE.IO.IOUtils import json_handler
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import GroupingLevels

if TYPE_CHECKING:
    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class Mapper(ABC):
    """Base class for mapping types."""

    def __init__(self):
        self._original_map = {}
        self._new_map = {}

    def get_full_setting(self) -> dict[int, float]:
        """
        Get resultant setting map.

        Returns
        -------
        dict[int, float]
            The full mapping.
        """
        return self._original_map | self._new_map

    def get_setting(self) -> dict[int, float]:
        """
        Get overridden settings.

        Returns
        -------
        dict[int, float]
            The minimal overridden settings.
        """
        return {
            key: self._new_map[key] for key in self._original_map.keys() & self._new_map
        }

    def get_json_setting(self) -> str:
        """
        Get settings as JSON string.

        Returns
        -------
        str
            A json string of the minimal mapping.
        """
        return json.dumps(self.get_setting())

    @staticmethod
    def get_selector(selection_string: str | Path | dict) -> ReusableSelection:
        """Get a reusable selector for the mapping.

        Parameters
        ----------
        selection_string : str | Path | dict
            Selection as JSON.

        Returns
        -------
        ReusableSelection
            Selector.

        Raises
        ------
        ConfigError
            If invalid selection JSON.
        """
        selector = ReusableSelection()
        try:
            selection = json_handler(selection_string)
        except Exception as err:
            raise ConfigError("Failed to get selection dict.") from err
        selector.load_from_dict(selection)

        return selector

    def reset(self) -> None:
        """Resets the setting."""
        self._new_map = {}

    @abstractmethod
    def apply(self, selection_string: Path | str | dict, *args, **kwargs): ...


AM = TypeVar("AM", default=dict[str, dict[str, str]])


class AtomMapping(ConfigureDescriptor[dict | str, dict[str, dict[str, str]], AM]):
    """Parameter for mapping from species to species."""

    default_tooltip = "Mapping of index to new species"

    def __init__(self, default: dict[str, dict[str, str]] | str = "{}", **kwargs):
        super().__init__(default=default, **kwargs)

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def validate(
        self, value: dict | str, deps: Depends, /
    ) -> dict[str, dict[str, str]]:
        if not value or value == "{}":
            return {}

        file_info = deps["trajectory"]
        try:
            value = json_handler(value)
        except Exception as err:
            raise ConfigError("Failed to get replacement values.") from err

        labels = file_info.labels

        try:
            fill_remaining_labels(value, labels)
        except AttributeError as err:
            raise ConfigError("Unable to map all atoms.") from err

        if not check_mapping_valid(value, labels):
            raise ConfigError("Atom mapping not valid.")

        return value


AS = TypeVar("AS", default=list[int])
ViableAS: TypeAlias = (
    Sequence[int] | dict[str, SelectionOperations] | Literal["all"] | Path | None
)


class AtomSelection(ConfigureDescriptor[ViableAS, list[int], AS]):
    """Selects atoms in trajectory based on the input string.

    This configurator allows the selection of a specific set of
    atoms on which the analysis will be performed. The defaults setting
    selects all atoms.

    Attributes
    ----------
    default : Collection[int] | dict | None
        The defaults selection setting.
    """

    SELECT_ALL: dict[str, SelectionOperations] = {
        "0": {"function_name": "select_all", "operation_type": "union"},
        "1": {"function_name": "select_dummy", "operation_type": "difference"},
    }

    def __init__(self, default: Collection[int] | dict | None = None, **kwargs):
        if default is None:
            default = self.SELECT_ALL

        super().__init__(default=default, **kwargs)
        self.all = False

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def validate(
        self,
        value: ViableAS,
        deps: Depends,
        /,
    ) -> list[int]:
        trajectory = deps["trajectory"]

        if value == "all":
            value = self.SELECT_ALL
        elif value is None:
            value = self.default
        elif isinstance(value, list | tuple | set):
            value = {
                "0": {
                    "function_name": "select_atoms",
                    "index_list": sorted(value),
                    "operation_type": "set",
                },
            }

        try:
            selection = json_handler(value)
        except Exception as err:
            raise ConfigError("Failed to get selection dict.") from err

        selector = ReusableSelection()
        try:
            selector.load_from_dict(selection)
        except TypeError as err:
            raise ConfigError("Unable to load from dictionary.") from err

        indices = selector.select_in_trajectory(trajectory)

        return sorted(indices)

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self) -> str:
        return super().__repr__()

    def full_repr(self) -> str: ...


PC = TypeVar("PC", default=dict[int, float])


class PartialCharge(ConfigureDescriptor[str | Path | dict, dict[int, float], PC]):
    """The partial charge mapper. Updates an atom partial charge map
    with applications of the update_charges method with a selection
    setting and partial charge."""

    def __init__(self, *args, default: str | Path | dict = "{}", **kwargs):
        super().__init__(*args, default=default, **kwargs)

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def validate(
        self,
        value: str | Path | dict,
        deps: Depends,
        /,
    ) -> dict[int, float]:
        try:
            value = json_handler(value)
        except Exception as err:
            raise ConfigError("Failed to get partial charge dict.") from err

        processed_values = {}
        for key, val in value.items():
            if isinstance(val, Collection):
                try:
                    charge = float(key)
                except (TypeError, ValueError) as err:
                    raise ConfigError(
                        f"Wrong charge {key} in the charge dictionary"
                    ) from err

                processed_values.update(dict.fromkeys(map(int, val), charge))
                continue

            try:
                index, charge = int(key), float(val)
            except (TypeError, ValueError) as err:
                raise ConfigError(
                    f"Index/charge pair {key}/{val} is not a valid int/float pair."
                ) from err
            processed_values[index] = charge

        system = deps["trajectory"].chemical_system

        if not processed_values.keys() <= set(system._atom_indices):
            LOG.warning("At least one atom index not found in the current system.")

        return {
            ind: processed_values[ind]
            for ind in processed_values.keys() & system._atom_indices
        }


class PartialChargeMapper(Mapper):
    """The partial charge mapper.

    Updates an atom partial charge map with application of
    :meth:`apply` with a selection setting and partial
    charge.
    """

    def __init__(self, trajectory: Trajectory):
        """
        Parameters
        ----------
        system : ChemicalSystem
            The chemical system object.
        """
        super().__init__()
        system = trajectory.chemical_system
        self._traj_charges = trajectory.charges(0)[:]

        self._current_trajectory = trajectory
        self._original_map = {
            at_num: self._traj_charges[at_num]
            for at_num, at in enumerate(system.atom_list)
        }

    def apply(self, selection_string: Path | str | dict, charge: float) -> None:
        """Update the selector and then update the partial charge map.

        Parameters
        ----------
        selection_string : Path | str | dict
            The selection setting to get the indices to map the input
            partial charge.
        charge : float
            The partial charge to map the selected atoms to.
        """
        selector = self.get_selector(selection_string)
        indices = selector.select_in_trajectory(self._current_trajectory)
        self._new_map.update(dict.fromkeys(indices, charge))

    def get_grouped_setting(self) -> dict[tuple[int], float]:
        """Return a dict of groups of indices with the same charge.

        Returns
        -------
        dict[tuple[int], float]
            The minimal partial charge setting.
        """
        new_charges = self._traj_charges.copy()
        for k, v in self._new_map.items():
            new_charges[k] = v

        valid_indices = set(*np.where(~np.isclose(new_charges, self._traj_charges)))

        buck = bucket(enumerate(new_charges), key=lambda x: x[1])
        return {key: [x for x, _ in buck[key] if x in valid_indices] for key in buck}

    def get_json_setting(self) -> str:
        """
        Returns
        -------
        str
            A json string of the minimal partial charge setting.
        """
        return json.dumps(self.get_grouped_setting())


GL = TypeVar("GL", default=GroupingLevels)


class GroupingLevel(SingleChoice[GroupingLevels | str, GroupingLevels, GL]):
    """Grouping level selector."""

    def __init__(
        self,
        *args,
        choices: None = None,
        default: GroupingLevels | str = GroupingLevels.ATOM,
        **kwargs,
    ):
        if choices is not None:
            raise ConfigError(f"Cannot provide choices to {type(self).__name__}")

        super().__init__(
            *args,
            choices=GroupingLevels,
            default=default,
            **kwargs,
        )

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def validate(
        self,
        value: GroupingLevels | str,
        deps: Depends,
        /,
    ) -> str:
        value = super().validate(value, deps)

        if (
            value is GroupingLevels.MOLECULE
            and not deps["trajectory"].chemical_system.unique_molecules()
        ):
            raise ConfigError("Requested molecule grouping, but no molecules exist")

        return value


class AtomTransmuter(Mapper):
    """The atom transmuter setting generator.

    Updates an atom transmutation setting with application of
    :meth:`apply_transmutation` with a selection setting and symbol.
    """

    def __init__(self, trajectory: Trajectory) -> None:
        """
        Parameters
        ----------
        system : ChemicalSystem
            The chemical system object.
        """
        super().__init__()
        self._current_trajectory = trajectory
        self._original_map = dict(enumerate(trajectory.chemical_system.atom_list))

    def apply(self, selection_string: str, symbol: str) -> None:
        """Update selector and then update the transmutation map.

        Parameters
        ----------
        selection_string : str
            the JSON string of the selection operation to use.
        symbol : str
            The element to map the selected atoms to.
        """
        if symbol not in ATOMS_DATABASE:
            raise ValueError(f"{symbol} not found in the atom database.")

        selector = self.get_selector(selection_string)
        indices = selector.select_in_trajectory(self._current_trajectory)
        self._new_map.update(dict.fromkeys(indices, symbol))


AT = TypeVar("AT", default=dict[int, str])


class AtomTransmutation(ConfigureDescriptor[dict | str | Path, dict[int, str], AT]):
    def __init__(self, default: dict[int, str] | None = None, **kwargs):
        if default is None:
            default = {}
        super().__init__(default=default, **kwargs)

    def validate(
        self,
        value: dict[int, str] | str | Path,
        deps: Depends,
        /,
    ):
        try:
            value = json_handler(value)
        except Exception as err:
            raise ConfigError("Failed to get transmutation dict.") from err

        if not value:
            return value

        try:
            value: dict[int, str] = {
                int(idx): element for idx, element in value.items()
            }
        except ValueError as err:
            raise ConfigError(
                "Keys of transmutation map should be castable to `int`"
            ) from err

        system = deps["trajectory"].chemical_system
        idxs = range(system.total_number_of_atoms)

        if missing := value.keys() - idxs:
            raise ConfigError(
                f"Input setting not valid - atom indices ({', '.join(map(str, missing))}) not found in the current system."
            )

        elements = set(value.values())
        known_atoms = set(deps["trajectory"].atoms) | set(ATOMS_DATABASE.atoms)

        if missing := elements - known_atoms:
            raise ConfigError(
                f"Elements ({', '.join(missing)}) not registered in the database"
            )

        return value
