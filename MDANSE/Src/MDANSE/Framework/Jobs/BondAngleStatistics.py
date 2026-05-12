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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia
from MDANSE.MolecularDynamics.Trajectory import Trajectory


def molecule_indices_in_selection(
    mol_name: str, traj_instance: Trajectory
) -> list[int]:
    selected_atoms = set(traj_instance.atom_indices)
    return [
        index
        for index, cluster in enumerate(
            traj_instance.chemical_system._clusters[mol_name]
        )
        if set(cluster).issubset(selected_atoms)
    ]


class BondAngleStatistics(IJob):
    """ """

    label = "Bond Angle Statistics"

    category = (
        "Analysis",
        "Structure",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["bond_1"] = (
        "AxisSelectionConfigurator",
        {
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["bond_2"] = (
        "AxisSelectionConfigurator",
        {
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": """\
{
   "0": {"function_name": "select_all", "operation_type": "union"}
}""",
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.molecule_type_1 = self.configuration["bond_1"]["value"]
        self.molecules_1 = molecule_indices_in_selection(
            self.molecule_type_1, self.trajectory
        )

        self.molecule_type_2 = self.configuration["bond_2"]["value"]
        self.molecules_2 = molecule_indices_in_selection(
            self.molecule_type_2, self.trajectory
        )

        self.bond1_index1 = self.configuration["bond_1"]["index1"]
        self.bond1_index2 = self.configuration["bond_1"]["index2"]

        self.bond2_index1 = self.configuration["bond_2"]["index1"]
        self.bond2_index2 = self.configuration["bond_2"]["index2"]

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._outputData.add(
            "bas/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "bas/axes/mol1_index",
            "LineOutputVariable",
            self.molecules_1,
            units="au",
        )

        self._outputData.add(
            "bas/axes/mol2_index",
            "LineOutputVariable",
            self.molecules_2,
            units="au",
        )

        self._outputData.add(
            "bas/bond_length/bond1",
            "SurfaceOutputVariable",
            (len(self.configuration["frames"]["duration"]), len(self.molecules_1)),
            axis="bas/axes/time|bas/axes/mol1_index",
            units="nm",
        )

        self._outputData.add(
            "bas/bond_length/bond2",
            "SurfaceOutputVariable",
            (len(self.configuration["frames"]["duration"]), len(self.molecules_2)),
            axis="bas/axes/time|bas/axes/mol2_index",
            units="nm",
        )

        self._outputData.add(
            "bas/bond_angle/all",
            "VolumeOutputVariable",
            (
                len(self.configuration["frames"]["duration"]),
                len(self.molecules_1),
                len(self.molecules_2),
            ),
            axis="bas/axes/time|bas/axes/mol1_index|bas/axes/mol2_index",
            units="degree",
        )

        self._outputData.add(
            "bas/bond_angle/diagonal",
            "SurfaceOutputVariable",
            (
                len(self.configuration["frames"]["duration"]),
                min(len(self.molecules_1), len(self.molecules_2)),
            ),
            axis="bas/axes/time|index",
            units="degree",
            main_result=True,
        )

    def run_step(self, index: int) -> tuple[int, list[np.ndarray]]:
        """Run the analysis for a single molecule.

        Parameters
        ----------
        index : int
            Index of the molecule in the chemical system.

        Returns
        -------
        tuple[int, list[np.ndarray]]
            Molecule index and the correlation arrays.

        """
        frame_index = self.configuration["frames"]["value"][index]
        coordinates = (
            self.trajectory.configuration(
                frame_index,
            )
            .continuous_configuration()
            .coordinates
        )
        bond_length_1 = np.empty(len(self.molecules_1))
        bond_length_2 = np.empty(len(self.molecules_2))
        angle_array = np.empty((len(self.molecules_1), len(self.molecules_2)))
        for nm1, mol1_index in enumerate(self.molecules_1):
            for nm2, mol2_index in enumerate(self.molecules_2):
                mol1 = self.trajectory.chemical_system._clusters[self.molecule_type_1][
                    mol1_index
                ]
                mol2 = self.trajectory.chemical_system._clusters[self.molecule_type_2][
                    mol2_index
                ]
                at1 = mol1[self.bond1_index1]
                at2 = mol1[self.bond1_index2]
                at3 = mol2[self.bond2_index1]
                at4 = mol2[self.bond2_index2]
                vec1 = coordinates[at2] - coordinates[at1]
                vec2 = coordinates[at4] - coordinates[at3]
                len_vec1 = np.linalg.norm(vec1)
                len_vec2 = np.linalg.norm(vec2)
                angle = np.dot(vec1, vec2) / (len_vec1 * len_vec2)
                bond_length_1[nm1] = len_vec1
                bond_length_2[nm2] = len_vec2
                angle_array[nm1, nm2] = angle

        return index, (bond_length_1, bond_length_2, np.degrees(np.arccos(angle_array)))

    def combine(self, frame_index: int, x: list[np.ndarray]):
        """Add the partial result to the results.

        Parameters
        ----------
        index : int
            index of the molecule
        x : list[np.ndarray]
            list of arrays of the correlation results

        """
        bl1, bl2, angle = x
        self._outputData["bas/bond_length/bond1"][frame_index, :] = bl1
        self._outputData["bas/bond_length/bond2"][frame_index, :] = bl2
        self._outputData["bas/bond_angle/all"][frame_index, :, :] = angle

    def finalize(self):
        """Normalise and write out the results."""

        self._outputData["bas/bond_angle/diagonal"][:, :] = np.diagonal(
            self._outputData["bas/bond_angle/all"][:], axis1=1, axis2=2
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
