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
from scipy.special import legendre

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia


class ReorientationalTimeCorrelationFunction(IJob):
    r"""Correlation of molecule's orientation in time.

    The result is a reorientational time-correlation function, which describes
    the change in orientation of a specific direction axis within a molecule.
    For one index, the axis will be defined by the positions of the atom with
    that index and the molecule's centre of mass.
    For two indices, the axis will be the vector between the atoms with these indices.
    If no indices are given, the shortest axis of the moment of inertia (pm1)
    will be used in the calculation. This will not be tied to specific atoms and
    will be sensitive to changes in the molecule's shape.

    In principle, reorientational time-correlation functions can be Legendre
    polynomials of different order. The results of this analysis correspond to
    the l=1 case.
    Angle at time T is calculated as the following: \n
    .. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
    .. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )

    The result is the
    #. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`

    **Usage:** \n
    This analysis is used to study molecule's orientation and rotation relaxation.
    """

    label = "Reorientational Time Correlation Function"

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
    settings["polynomial_order"] = (
        "IntegerConfigurator",
        {
            "label": "Maximum Legendre polynomial order to be used",
            "default": 1,
            "mini": 1,
            "maxi": 3,
        },
    )
    settings["per_axis"] = (
        "BooleanConfigurator",
        {"label": "output contribution per axis", "default": False},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.molecules = self.configuration["trajectory"][
            "instance"
        ].chemical_system._clusters[self.configuration["molecule_and_axis"]["value"]]

        self.inner_index1 = self.configuration["molecule_and_axis"]["index1"]
        self.inner_index2 = self.configuration["molecule_and_axis"]["index2"]

        self.numberOfSteps = len(self.molecules)
        self.legendre_order = self.configuration["polynomial_order"]["value"]

        self.masses = np.array(
            self.configuration["trajectory"]["instance"].chemical_system.atom_property(
                "atomic_weight",
            ),
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
                    self.configuration["molecule_and_axis"]["value"],
                ),
            ),
            units="au",
        )

        for l_order in range(1, self.legendre_order + 1):
            self._outputData.add(
                f"rtcf_l={l_order}",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="au",
                main_result=True,
            )

            if self.configuration["per_axis"]["value"]:
                self._outputData.add(
                    f"rtcf_l={l_order}_per_axis",
                    "SurfaceOutputVariable",
                    (
                        self.configuration["trajectory"][
                            "instance"
                        ].chemical_system.number_of_molecules(
                            self.configuration["molecule_and_axis"]["value"],
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
            ),
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index,
            )
            coordinates = configuration.contiguous_configuration().coordinates[molecule]
            if self.inner_index2 is not None:
                ref_pos = coordinates[self.inner_index2]
            else:
                centre_coordinates = center_of_mass(coordinates, masses)
                ref_pos = centre_coordinates
            if self.inner_index1 is None:
                moi = moment_of_inertia(
                    coordinates,
                    centre_coordinates,
                    masses,
                )
                _, eigenvectors = np.linalg.eigh(moi)
                if i > 0 and np.dot(diff[i - 1], eigenvectors[0]) < 0:
                    diff[i] = -eigenvectors[0]
                else:
                    diff[i] = eigenvectors[0]
                continue
            diff[i] = coordinates[self.inner_index1] - ref_pos
        modulus = np.sqrt(np.sum(diff**2, 1))

        diff /= modulus[:, np.newaxis]

        n_configs = self.configuration["frames"]["n_configs"]
        ac = correlate(diff, diff[:n_configs], mode="valid") / n_configs
        return index, ac.T[0]

    def combine(self, index: int, x: np.ndarray):
        """Add the partial result to the results.

        Parameters
        ----------
        index : int
            index of the molecule
        x : np.ndarray
            array of the correlation results

        """
        for l_order in range(1, self.legendre_order + 1):
            poly = legendre(l_order)
            self._outputData[f"rtcf_l={l_order}"] += poly(x)

            if self.configuration["per_axis"]["value"]:
                self._outputData[f"rtcf_l={l_order}_per_axis"][index, :] = poly(x)

    def finalize(self):
        """Normalise and write out the results."""
        for l_order in range(1, self.legendre_order + 1):
            self._outputData[f"rtcf_l={l_order}"] /= self.configuration["trajectory"][
                "instance"
            ].chemical_system.number_of_molecules(
                self.configuration["molecule_and_axis"]["value"],
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
