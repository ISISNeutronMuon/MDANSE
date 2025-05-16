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
from typing import Optional, Any
from enum import Enum, auto
from collections import Counter, defaultdict
from multiprocessing import Lock

import numpy as np

from MDANSE.MLogging import LOG
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem


class GroupingLevel(Enum):
    ATOM = auto()
    MOL_EACH = auto()
    MOL_AVERAGE = auto()


GROUPING_LABELS = {
    "atom": GroupingLevel.ATOM,
    "individual molecules": GroupingLevel.MOL_EACH,
    "average over molecules": GroupingLevel.MOL_AVERAGE,
}

DEFAULT_DATA_PARAMETERS = {
    "axis": "index",
    "units": "au",
    "main_result": True,
    "partial_result": True,
    "dtype": np.float64,
}


class GroupingTool:
    """Handles the analysis results and assigns the
    correct results to different datasets based on the grouping
    setting"""

    def __init__(self, chemical_system: ChemicalSystem, output_data: OutputData):
        """Set grouper up using trajectory topology.

        Parameters
        ----------
        chemical_system : ChemicalSystem
            information about atoms and molecules in the system
        output_data : OutputData
            structure into which to write the results of the calculation

        """
        self._cs = chemical_system
        self._output_data = output_data
        self._grouping = None
        self._data_parameters = {}
        self._weight_dictionary = {}
        self._mass_dictionary = {}
        self._molecule_mass = defaultdict(float)
        self._current_selection = set()
        self._indices_per_data_key = {}
        self._mandatory_keys = ["output_type", "dimensions"]
        self._extra_keys = ["axis", "units", "main_result", "partial_result", "dtype"]
        self._plain_datasets = set()
        self._weighted_datasets = set()
        self._molecule_datasets = set()
        self._mutex = Lock()
        self._debug_counter = Counter()

    def set_grouping(self, text_key: str):
        """Choose the level of grouping to use.

        This has to be configured before creating output data sets.

        Parameters
        ----------
        text_key : str
            name of the grouping level in GROUPING_LABELS

        """
        self._grouping = GROUPING_LABELS.get(text_key, GroupingLevel.ATOM)

    def set_weight_dictionary(self, new_weights: dict[tuple[str], float]):
        """Store the dictionary with weights per atom type.

        Parameters
        ----------
        new_weights : dict[tuple[str],float]
            dictionary of {atom_types: scaling_factor} pairs

        """
        self._weight_dictionary = {
            "".join(key): value for key, value in new_weights.items()
        }

    def set_atom_masses(self, atom_database):
        """Get atom masses from an object that has .get_atom_property.

        Parameters
        ----------
        atom_database : Union[AtomDatabase, Trajectory]
            any object that has get_atom_property

        """
        self._mass_dictionary = {
            atom_type: atom_database.get_atom_property(atom_type, "atomic_weight")
            for atom_type in self._cs._unique_elements
        }

    def set_dataset_parameters(self, parameters: dict[str, Any]):
        """Save information about axes, units and array dimensions.

        These will be used for all the output data.

        Parameters
        ----------
        parameters : dict[str, Any]
            dictionary of parameters needed by OutputData.write

        """
        if missing := self._mandatory_keys - parameters.keys():
            raise KeyError(
                f"Settings ({', '.join(missing)}) are missing from data parameters."
            )
        for key in self._mandatory_keys + self._extra_keys:
            self._data_parameters[key] = parameters.get(
                key, DEFAULT_DATA_PARAMETERS.get(key)
            )

    def set_selection(self, selected_indices: set[int]):
        """Save information about indices in the atom selection.

        Parameters
        ----------
        selected_indices : set[int]
            All the atom indices in the current selection

        """
        self._current_selection = set(selected_indices)

    def add_dataset(
        self,
        name,
        override: Optional[dict[str, Any]] = None,
        weight_key: Optional[str] = None,
    ):
        """Create an output dataset with a specific name.

        Parameters
        ----------
        name : _type_
            key used by the OutputData dictionary
        override : Optional[dict[str, Any]], optional
            keywords to be used by this dataset, by default None
        weight_key : Optional[str], optional
            scaling factor of this dataset, by default None

        """
        self._debug_counter[name] += 1
        pardict = {key: self._data_parameters[key] for key in self._extra_keys}
        if override is not None:
            pardict.update(override)
        self._output_data.add(
            name,
            self._data_parameters["output_type"],
            self._data_parameters["dimensions"],
            **pardict,
        )
        if weight_key:
            self._output_data[name].scaling_factor *= self._weight_dictionary[
                weight_key
            ]

    def create_result_groups(self, name: str):
        """Create all the output datasets.

        Parameters
        ----------
        name : str
            root of the dataset names

        Raises
        ------
        RuntimeError
            Other methods needed to be called before this one.

        """
        if self._data_parameters is None:
            raise RuntimeError("Creating output data groups without parameters.")
        if not self._current_selection:
            raise RuntimeError("Trying to group an empty selection.")
        self.create_atom_groups(name)
        if self._grouping is GroupingLevel.MOL_AVERAGE:
            self.create_averaged_molecule_groups(name)
        elif self._grouping is GroupingLevel.MOL_EACH:
            self.create_individual_molecule_groups(name)

    def create_atom_groups(self, name: str):
        """Create datasets for atom grouping.

        This will be called for every grouping level.

        Parameters
        ----------
        name : str
            root of the dataset names

        """
        for atom_type in self._cs._unique_elements:
            indices = self._current_selection.intersection(
                self._cs.element_indices[atom_type]
            )
            if indices:
                dset_name = f"{name}_{atom_type}"
                self.add_dataset(dset_name, weight_key=str(atom_type))
                self._output_data[dset_name].atom_indices = list(indices)
                self._indices_per_data_key[dset_name] = indices
                self._plain_datasets.add(dset_name)
        dset_name = f"{name}_total"
        self.add_dataset(dset_name, override={"partial_result": False})
        self._output_data[dset_name].atom_indices = list(self._current_selection)
        self._indices_per_data_key[dset_name] = self._current_selection
        self._weighted_datasets.add(dset_name)

    def create_averaged_molecule_groups(self, name: str):
        """Add datasets needed for results per molecule type.

        Only the molecules that are fully in the selection
        are included.

        Parameters
        ----------
        name : str
            root of the dataset names

        """
        molecules_dropped = []
        for molecule in self._cs.unique_molecules():
            all_indices = set()
            for mindex, mol in enumerate(self._cs._clusters[molecule]):
                trimmed_mol = self._current_selection.intersection(mol)
                if set(mol) == trimmed_mol:
                    all_indices |= mol
                elif trimmed_mol:
                    molecules_dropped.append(mindex)
            if all_indices:
                dset_name = f"{name}_{molecule}_all"
                self.add_dataset(dset_name)
                self._output_data[dset_name].atom_indices = list(all_indices)
                self._indices_per_data_key[dset_name] = all_indices
                self._molecule_datasets.add(dset_name)
        if molecules_dropped:
            LOG.warning(
                "Molecules %s were not fully selected and will be omitted",
                molecules_dropped,
            )

    def create_individual_molecule_groups(self, name: str):
        """Add datasets needed for results per EACH molecule.

        Only the molecules that are fully in the selection
        are included.

        Parameters
        ----------
        name : str
            root of the dataset names

        """
        molecules_dropped = []
        for molecule in self._cs.unique_molecules():
            for mindex, mol in enumerate(self._cs._clusters[molecule]):
                trimmed_mol = self._current_selection.intersection(mol)
                if set(mol) == trimmed_mol:
                    dset_name = f"{name}_{molecule}_{mindex + 1}"
                    self.add_dataset(dset_name, override={"main_result": False})
                    self._output_data[dset_name].atom_indices = list(trimmed_mol)
                    self._indices_per_data_key[dset_name] = trimmed_mol
                    self._molecule_datasets.add(dset_name)
                elif trimmed_mol:
                    molecules_dropped.append(mindex)
        if molecules_dropped:
            LOG.warning(
                "Molecules %s were not fully selected and will be omitted",
                molecules_dropped,
            )

    def assign_result(
        self,
        index: int,
        result: np.ndarray,
        *,
        normalise: bool = True,
        centre_of_mass: bool = True,
    ):
        """Add the current result to all the datasets that use it,
        together with the relevant scaling factors.

        Parameters
        ----------
        index : int
            index of the atom in the ChemicalSystem
        result : np.ndarray
            array with the calculation results.
        normalise : bool
            if True, result for each atom type will be divided by the
            number of atoms of this type
        centre_of_mass : bool
            if True, results for each atom of the molecule will be scaled
            by the atom mass

        """
        with self._mutex:
            self.assign_result_molecular(index, result, centre_of_mass)
            self.assign_result_atomic(index, result, normalise)

    def assign_result_molecular(
        self, index: int, result: np.ndarray, *, centre_of_mass: bool = True
    ):
        """Add the current result to the molecule-grouped datasets,
        together with the relevant scaling factors.

        Parameters
        ----------
        index : int
            index of the atom in the ChemicalSystem
        result : np.ndarray
            array with the calculation results.
        centre_of_mass : bool
            if True, results for each atom of the molecule will be scaled
            by the atom mass

        """
        for dset_name in self._molecule_datasets:
            indices = self._indices_per_data_key[dset_name]
            if index in indices:
                atom_type = self._cs._atom_types[index]
                if centre_of_mass:
                    atom_mass = self._mass_dictionary[atom_type]
                    self._output_data[dset_name] += result * atom_mass
                    self._molecule_mass[dset_name] += atom_mass
                else:
                    self._output_data[dset_name] += result
                    self._molecule_mass[dset_name] += 1.0

    def assign_result_atomic(
        self, index: int, result: np.ndarray, *, normalise: bool = True
    ):
        """Add the current result to the atom-averaged datasets,
        together with the relevant scaling factors.

        Parameters
        ----------
        index : int
            index of the atom in the ChemicalSystem
        result : np.ndarray
            array with the calculation results.
        normalise : bool
            if True, result for each atom type will be divided by the
            number of atoms of this type

        """
        for dset_name in self._plain_datasets:
            indices = self._indices_per_data_key[dset_name]
            if index in indices:
                if normalise:
                    result /= len(indices)
                self._output_data[dset_name] += result
        for dset_name in self._weighted_datasets:
            indices = self._indices_per_data_key[dset_name]
            if index in indices:
                atom_type = self._cs._atom_types[index]
                self._output_data[dset_name] += (
                    result * self._weight_dictionary[atom_type]
                )

    def finalise_centre_of_mass(self, exponent: float = 1.0):
        """Normalise the results grouped per molecule.

        Divides either by the total mass of the molecule,
        or by the total number of atoms in the molecule.
        It can also square-root the results (used by
        Root Mean Square Displacement.)

        Parameters
        ----------
        exponent : float, optional
            if square root is needed, set to 0.5, by default 1.0

        """
        for dset_name in self._molecule_datasets:
            norm = self._molecule_mass[dset_name]
            if np.isclose(norm, 0):
                norm = 1.0
            self._output_data[dset_name] /= norm
            if np.isclose(exponent, 1.0):
                continue
            elif np.isclose(exponent, 0.5):
                self._output_data[dset_name][:] = np.sqrt(self._output_data[dset_name])
            else:
                self._output_data[dset_name][:] = (
                    self._output_data[dset_name] ** exponent
                )
