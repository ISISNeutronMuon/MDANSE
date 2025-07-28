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

import collections

import numpy as np
from scipy.signal import correlate
from scipy.special import legendre

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia


def correlate_legendre(
    signal: np.ndarray, corr_window: int, poly_order: int
) -> np.ndarray:
    """Calculate the

    Parameters
    ----------
    signal : np.ndarray
        An (N,3) array of orientation vectors
    corr_window : int
        Size of the moving correlation window
    poly_order : int
        Order of the Legendre polynomial

    Returns
    -------
    np.ndarray
        An (N - corr_window + 1,) array of correlation results

    """
    array_length = len(signal)
    result_length = array_length - corr_window + 1
    poly = legendre(poly_order)
    results = np.zeros(result_length)
    for t0 in range(corr_window):
        results += poly(np.dot(signal[t0], signal[t0 : t0 + result_length].T))
    return results / corr_window


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
    polynomials of different order. At the moment, this analysis will calculate
    all the orders up the maximum Legendre polynomial order specified as one
    of the input parameters.

    Angle at time :math:`t` is calculated as the following:

    .. math::
        \hat{\mathbf{n}}(t) =  \frac{\mathbf{r}_{i}(t) - \mathbf{r}_{j}(t)}{\vert \mathbf{r}_{i}(t) - \mathbf{r}_{j}(t) \vert}

    .. math::
        \phi(t = t_{1}-t_{0}) = \arccos( \hat{\mathbf{n}}(t_{1}) \cdot \hat{\mathbf{n}}(t_{0}))

    The general result is :math:`C_{l}(t) = \langle P_{l}[\cos(\phi(t))] \rangle`,
    where :math:`P_{l}[x]` is the Legendre polynomial of the order :math:`l`.
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
            "default": 2,
            "mini": 1,
            "maxi": 6,
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

        self.legendre_order = self.configuration["polynomial_order"]["value"]
        self.numberOfSteps = len(self.molecules)

        self.masses = np.array(
            self.trajectory.chemical_system.atom_property(
                "atomic_weight",
            ),
        )

        self._outputData.add(
            "rtcf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "rtcf/axes/axis_index",
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
                f"rtcf/l={l_order}",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="rtcf/axes/time",
                units="au",
                main_result=True,
            )

            if self.configuration["per_axis"]["value"]:
                self._outputData.add(
                    f"rtcf/per_axis/l={l_order}",
                    "SurfaceOutputVariable",
                    (
                        self.configuration["trajectory"][
                            "instance"
                        ].chemical_system.number_of_molecules(
                            self.configuration["molecule_and_axis"]["value"],
                        ),
                        self.configuration["frames"]["n_frames"],
                    ),
                    axis="rtcf/axes/axis_index|rtcf/axes/time",
                    units="au",
                    main_result=True,
                    partial_result=True,
                )

    @property
    def legendre_orders(self):
        return range(1, self.legendre_order + 1)

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
            configuration = self.trajectory.configuration(
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
        modulus = np.linalg.norm(diff, axis=1)

        diff /= modulus[:, np.newaxis]

        n_configs = self.configuration["frames"]["n_configs"]
        results = []
        for legendre_order in self.legendre_orders:
            if legendre_order == 1:
                ac = correlate(diff, diff[:n_configs], mode="valid") / n_configs
                results.append(ac.T[0])
            else:
                ac = correlate_legendre(
                    diff, corr_window=n_configs, poly_order=legendre_order
                )
                results.append(ac)
        return index, results

    def combine(self, index: int, x: list[np.ndarray]):
        """Add the partial result to the results.

        Parameters
        ----------
        index : int
            index of the molecule
        x : list[np.ndarray]
            list of arrays of the correlation results

        """
        for l_order in self.legendre_orders:
            self._outputData[f"rtcf/l={l_order}"] += x[l_order - 1]

            if self.configuration["per_axis"]["value"]:
                self._outputData[f"rtcf/per_axis/l={l_order}"][index, :] = x[
                    l_order - 1
                ]

    def finalize(self):
        """Normalise and write out the results."""
        for l_order in self.legendre_orders:
            self._outputData[f"rtcf/l={l_order}"] /= self.configuration["trajectory"][
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

        self.trajectory.close()
        super().finalize()
