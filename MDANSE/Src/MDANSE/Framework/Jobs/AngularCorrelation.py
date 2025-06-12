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

import collections

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia


class AngularCorrelation(IJob):
    """
    Computes the angular correlation for a vector defined with respect to a molecule or set of molecules.

    Vector defined by user, starting at the origin pointing in a particular direction.
    Origin and direction can either be an atom or a centre definition (centre of a group of atoms). For example, the origin
    could be defined by the geometric centre of the head group of a surfactant molecule and the direction simply by the last atom
    of the tail or chain. The correlation is calculated for the angle formed by the same vector at
    different times

    **Calculation:** \n
    angle at time T is calculated as the following: \n
    .. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
    .. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )

    **Output:** \n
    #. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`
    #. angular_correlation_legendre_2nd: :math:`<\\frac{1}{2}(3cos(\phi(T))^{2}-1)>`

    **Usage:** \n
    This analysis is used to study molecule's orientation and rotation relaxation.
    """

    label = "Angular Correlation"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["molecule_and_axis"] = (
        "AxisSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["per_axis"] = (
        "BooleanConfigurator",
        {"label": "output contribution per axis", "default": False},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.molecules = self.configuration["trajectory"][
            "instance"
        ].chemical_system._clusters[self.configuration["molecule_and_axis"]["value"]]

        self.inner_index1 = self.configuration["molecule_and_axis"]["index1"]
        self.inner_index2 = self.configuration["molecule_and_axis"]["index2"]

        self.numberOfSteps = len(self.molecules)

        self.masses = np.array(
            self.configuration["trajectory"]["instance"].chemical_system.atom_property(
                "atomic_weight"
            )
        )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "axis_index",
            "LineOutputVariable",
            np.arange(
                self.configuration["trajectory"][
                    "instance"
                ].chemical_system.number_of_molecules(
                    self.configuration["molecule_and_axis"]["value"]
                )
            ),
            units="au",
        )

        self._outputData.add(
            "ac",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
            units="au",
            main_result=True,
        )

        if self.configuration["per_axis"]["value"]:
            self._outputData.add(
                "ac_per_axis",
                "SurfaceOutputVariable",
                (
                    self.configuration["trajectory"][
                        "instance"
                    ].chemical_system.number_of_molecules(
                        self.configuration["molecule_and_axis"]["value"]
                    ),
                    self.configuration["frames"]["n_frames"],
                ),
                axis="axis_index|time",
                units="au",
                main_result=True,
                partial_result=True,
            )

    def run_step(self, index: int) -> tuple[int, np.ndarray]:
        """Run the analysis for a single molecule.

        Parameters
        ----------
        index : int
            Index of the molecule in the chemical system.

        Returns
        -------
        tuple[int, np.ndarray]
            Molecule index and the correlation array.
        """

        molecule = self.molecules[index]
        masses = self.masses[molecule]

        diff = np.empty((self.configuration["frames"]["number"], 3))

        for i, frame_index in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            )
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index
            )
            coordinates = configuration.contiguous_configuration().coordinates[molecule]
            if self.inner_index2 is not None:
                ref_pos = coordinates[self.inner_index2]
            else:
                centre_coordinates = center_of_mass(coordinates, masses)
                ref_pos = centre_coordinates
            if self.inner_index1 is None:
                pm1, _, _ = moment_of_inertia(
                    coordinates, centre_coordinates, masses, output_eigenvectors=True
                )
                diff[i] = pm1
                continue
            diff[i] = coordinates[self.inner_index1] - ref_pos

        modulus = np.sqrt(np.sum(diff**2, 1))

        diff /= modulus[:, np.newaxis]

        n_configs = self.configuration["frames"]["n_configs"]
        ac = correlate(diff, diff[:n_configs], mode="valid") / (3 * n_configs)
        return index, ac.T[0]

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["ac"] += x

        if self.configuration["per_axis"]["value"]:
            self._outputData["ac_per_axis"][index, :] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._outputData["ac"] /= self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_molecules(
            self.configuration["molecule_and_axis"]["value"]
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
