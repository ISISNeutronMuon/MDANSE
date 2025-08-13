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
from typing import Any

import h5py

from MDANSE.Framework.AtomSelector.atom_selection import select_atoms, select_dummy
from MDANSE.Framework.AtomSelector.general_selection import (
    invert_selection,
    select_all,
    select_none,
    toggle_selection,
)
from MDANSE.Framework.AtomSelector.group_selection import select_labels, select_pattern
from MDANSE.Framework.AtomSelector.molecule_selection import select_molecules
from MDANSE.Framework.AtomSelector.spatial_selection import (
    select_positions,
    select_sphere,
)
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory

function_lookup = {
    function.__name__: function
    for function in [
        select_all,
        select_none,
        invert_selection,
        select_atoms,
        select_dummy,
        select_molecules,
        select_labels,
        select_pattern,
        select_positions,
        select_sphere,
    ]
}


class ReusableSelection:
    """Stores an applies atom selection operations.

    A reusable sequence of operations which, when applied
    to a trajectory, returns a set of atom indices based
    on the specified criteria.

    """

    def __init__(self) -> None:
        """Create an empty selection.

        Parameters
        ----------
        trajectory: Trajectory
            The chemical system to apply the selection to.

        """
        self.reset()

    def reset(self):
        """Initialise the attributes to an empty list of operations."""
        self.system = None
        self.trajectory = None
        self.all_idxs = set()
        self.operations = {}

    def set_selection(
        self,
        *,
        number: int | None = None,
        function_parameters: dict[str, Any],
    ):
        """Append a new selection operation, or overwrite an existing one.

        Parameters
        ----------
        number : Union[int, None], optional
            the position of the new selection in the sequence of operations
        function_parameters : Dict[str, Any], optional
            the dictionary of keyword arguments defining a selection operation

        """
        number = int(number) if number is not None else len(self.operations)
        self.operations[number] = function_parameters

    def apply_single_selection(
        self,
        function_parameters: dict[str, Any],
        trajectory: Trajectory,
        selection: set[int],
    ) -> set[int]:
        """Modify the input selection based on input parameters.

        This method applied a single selection operation to
        an already exising selection for a specific trajectory.

        Parameters
        ----------
        function_parameters : dict[str, Any]
            All the inputs needed to call an atom selection function
        trajectory : Trajectory
            Instance of the trajectory in which we are selecting atoms
        selection : set[int]
            indices of atoms that resulted from previous steps

        Returns
        -------
        set[int]
            indices of selected atoms from all operations so far

        """
        function_name = function_parameters.get("function_name", "select_all")
        if function_name == "invert_selection":
            new_selection = self.all_idxs.difference(selection)
        elif function_name == "toggle_selection":
            new_selection = toggle_selection(
                trajectory,
                selection,
                function_parameters.get("clicked_atoms", []),
            )
        else:
            operation_type = function_parameters.get("operation_type", "union")
            function = function_lookup[function_name]
            temp_selection = function(trajectory, **function_parameters)
            if operation_type == "union":
                new_selection = selection | temp_selection
            elif operation_type == "intersection":
                new_selection = selection & temp_selection
            elif operation_type == "difference":
                new_selection = selection - temp_selection
            else:
                new_selection = temp_selection
        return new_selection

    def validate_selection_string(
        self,
        json_string: str,
        trajectory: Trajectory,
        current_selection: set[int],
    ) -> bool:
        """Check if the new selection string changes the current selection.

        Checks if the selection operation encoded in the input JSON string
        will add any new atoms to the current selection on the given trajectory.

        Parameters
        ----------
        json_string : str
            new selection operation in a JSON string
        trajectory : Trajectory
            a trajectory instance for which current_selection is defined
        current_selection : Set[int]
            set of currently selected atom indices

        Returns
        -------
        bool
            True if the operation changes selection, False otherwise

        """
        function_parameters = json.loads(json_string)
        if not self.operations:
            return True
        operation_type = function_parameters.get("operation_type", "union")
        selection = self.apply_single_selection(
            function_parameters,
            trajectory,
            current_selection,
        )
        return ((selection - current_selection) and operation_type == "union") or (
            (current_selection - selection) and operation_type != "union"
        )

    def select_in_trajectory(self, trajectory: Trajectory) -> set[int]:
        """Select atoms in the input trajectory.

        Applies all the selection operations in sequence to the
        input trajectory, and returns the resulting set of indices.

        Parameters
        ----------
        trajectory : Trajectory
            trajectory object in which the atoms will be selected

        Returns
        -------
        set[int]
            set of atom indices that have been selected in the input trajectory

        """
        selection = set()
        self.all_idxs = trajectory.chemical_system.all_indices
        sequence = sorted(map(int, self.operations))
        if not sequence:
            return self.all_idxs
        for number in sequence:
            function_parameters = self.operations[number]
            selection = self.apply_single_selection(
                function_parameters,
                trajectory,
                selection,
            )
        return selection

    def convert_to_json(self) -> str:
        """Output all the operations as a JSON string.

        For the purpose of storing the selection independent of the
        trajectory it is acting on, this method encodes the sequence
        of selection operations as a string.

        Returns
        -------
        str
            All the operations of this selection, encoded as string

        """
        return json.dumps(self.operations)

    def load_from_json(self, json_string: str):
        """Populate the operations sequence from the input string.

        Loads the atom selection operations from a JSON string.
        Adds the operations to the selection sequence.

        Parameters
        ----------
        json_string : str
            A sequence of selection operations, encoded as a JSON string

        """
        json_setting = json.loads(json_string)
        self.load_from_dict(json_setting)

    def load_from_json_file(self, filename: Path | str):
        """Load a selection from a JSON text file.

        Parameters
        ----------
        filename : Path | str
            name of a text file containing just a selection in JSON format

        """
        with open(filename) as source:
            json_setting = json.load(source)
            self.load_from_dict(json_setting)

    def load_from_dict(self, value: dict) -> None:
        """Load a selection from a dictionary.

        Parameters
        ----------
        value : dict
            Dictionary of substitutions.

        """
        for k0, v0 in value.items():
            if not isinstance(v0, dict):
                raise TypeError(f"Selection {v0} is not a dictionary.")
            self.set_selection(number=k0, function_parameters=v0)

    def save_to_json_file(self, filename: Path | str):
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
            json.dump(self.operations, target)

    def load_from_hdf5(self, filename: str):
        """Load selection from an HDF5 output file (MDA format).

        Parameters
        ----------
        filename : str
            path to an MDA file, given as string

        """
        with h5py.File(filename) as source:
            try:
                byte_string = source["metadata/inputs/atom_selection"][0]
            except KeyError:
                LOG.warning(f"atom selection string not found in file {filename}")
                json_string = "{}"
            else:
                json_string = json.loads(byte_string.decode())
            self.load_from_json(json_string)
