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

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import (
    ChemicalSystem,
    assign_molecules_after_atom_selection,
)
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    Array,
    AtomSelection,
    AtomTransmutation,
    Float,
    FrameSelect,
    MDANSETrajectory,
    OutputTrajectory,
    PartialCharge,
    to_class,
)
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TrajectoryEditor(IJob):
    """Write out a modified version of the input trajectory.

    At the moment, the main applications include:

    - molecule detection,
    - setting unit cell parameters,
    - setting partial charges,
    - removing or transmuting atoms,
    - removing frames.
    """

    label = "Trajectory Editor"

    category = ("Trajectory",)
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    unit_cell = Array[UnitCell | None](
        optional=True,
        default=None,
        non_zero=True,
        on_set=to_class(UnitCell),
        shape=(3, 3),
    )
    atom_selection = AtomSelection(
        depends={"trajectory": "trajectory"},
        default={"0": {"function_name": "select_all", "operation_type": "union"}},
    )
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    atom_charges = PartialCharge(depends={"trajectory": "trajectory"}, default={})
    molecule_tolerance = Float[float | None](
        optional=True,
        default=None,
        tooltip="Accept bonds for distances lower than sum of the covalent radii and this tolerance margin",
        label="Search for molecules (covalent radii plus the tolerance in nm)",
        minimum=0.0,
    )
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = len(self.frames)
        self._input_trajectory = self.trajectory
        self._input_chemical_system = self.trajectory.chemical_system

        if self.unit_cell is not None:
            self._input_trajectory._trajectory._unit_cells = [self.unit_cell] * len(
                self.trajectory
            )

        # The collection of atoms corresponding to the atoms selected for output.
        indices = self.trajectory.atom_indices
        self._indices = indices
        temp_copy = list(self._input_chemical_system.atom_list)

        indices_per_element = self.trajectory.get_indices()

        for element, numbers in indices_per_element.items():
            for num in numbers:
                temp_copy[num] = element

        self._selectedAtoms = [temp_copy[ind] for ind in indices]
        name_list = [self._input_chemical_system.name_list[ind] for ind in indices]

        new_chemical_system = ChemicalSystem("Edited system")
        new_chemical_system.initialise_atoms(self._selectedAtoms, name_list)
        if self.molecule_tolerance is not None:
            tolerance = self.molecule_tolerance
            conn = Connectivity(
                trajectory=self._input_trajectory, selection=indices, parallel_workers=1
            )
            conn.find_bonds(tolerance=tolerance)
            conn.add_bond_information(new_chemical_system)
            conf = self.trajectory.configuration(self.frames[0].ind)
            coords = conf.coordinates[indices]
            if conf.is_periodic:
                com_conf = PeriodicRealConfiguration(
                    new_chemical_system,
                    coords,
                    conf.unit_cell,
                )
            else:
                com_conf = RealConfiguration(
                    new_chemical_system,
                    coords,
                )
            coords = com_conf.contiguous_configuration().coordinates
        else:
            assign_molecules_after_atom_selection(
                self._indices, self._input_chemical_system, new_chemical_system
            )

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.output_files.path,
            new_chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. None
        """
        # get the Frame index
        frame = self.frames[index]
        frameIndex = frame.ind
        time = frame.time

        conf = self.trajectory.configuration(frameIndex)
        conf = conf.contiguous_configuration(bring_to_centre=True)
        charges = self.trajectory.charges(frameIndex)
        coords = conf.coordinates

        variables = {}
        if self.trajectory.has_variable("velocities"):
            variables["velocities"] = self.trajectory.variable("velocities")[
                frameIndex, self._indices, :
            ].astype(np.float64)
        if self.trajectory.has_variable("gradients"):
            variables["gradients"] = self.trajectory.variable("gradients")[
                frameIndex, self._indices, :
            ].astype(np.float64)

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system,
                coords[self._indices],
                conf.unit_cell,
                **variables,
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system,
                coords[self._indices],
                **variables,
            )

        new_charges = np.zeros(len(self._indices))
        for number, at_index in enumerate(self._indices):
            new_charges[number] = self.atom_charges.get(at_index, charges[at_index])

        # The times corresponding to the running index.
        self._output_trajectory.dump_configuration(com_conf, time)
        self._output_trajectory.write_charges(new_charges, index)

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The index of the step.
        x : Any
            The returned result(s) of run_step.
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # The output trajectory is closed.
        self._output_trajectory.write_standard_atom_database()
        write_metadata(self, self._output_trajectory._h5_file)
        self._output_trajectory.close()
        super().finalize()
