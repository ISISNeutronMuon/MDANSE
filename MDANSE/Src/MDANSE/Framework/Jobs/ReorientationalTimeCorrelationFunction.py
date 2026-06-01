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
from scipy.signal import correlate
from scipy.special import legendre

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    Boolean,
    CorrelationWindow,
    FrameSelect,
    Integer,
    MDANSETrajectory,
    MolecularAxis,
    OutputFile,
    RunningMode,
)
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
    PREDICTORS = ("frame_window",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory()
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    molecule_and_axis = MolecularAxis(
        depends={"choices": "trajectory", "trajectory": "trajectory"}
    )
    legendre_order = Integer(
        label="Maximum Legendre polynomial order to be used",
        default=2,
        minimum=1,
        maximum=6,
        tooltip="All the orders up to this one will be calculated.",
    )
    per_axis = Boolean(label="Decompose the results into per-axis contributions")
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.molecules = self.trajectory.chemical_system._clusters[
            self.molecule_and_axis.molecule
        ]

        self.n_molecules = self.trajectory.chemical_system.number_of_molecules(
            self.molecule_and_axis.molecule
        )
        self.inner_index1 = self.molecule_and_axis.axis_1
        self.inner_index2 = self.molecule_and_axis.axis_2

        self.numberOfSteps = len(self.molecules)

        self.masses = np.array(
            self.trajectory.chemical_system.atom_property("atomic_weight"),
        )

        self._outputData.add(
            "rtcf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )

        self._outputData.add(
            "rtcf/axes/axis_index",
            "LineOutputVariable",
            np.arange(self.n_molecules),
            units="au",
        )

        for l_order in self.legendre_orders:
            self._outputData.add(
                f"rtcf/l={l_order}",
                "LineOutputVariable",
                (self.frame_window.window,),
                axis="rtcf/axes/time",
                units="au",
                main_result=True,
            )

            if self.per_axis:
                self._outputData.add(
                    f"rtcf/per_axis/l={l_order}",
                    "SurfaceOutputVariable",
                    (self.n_molecules, self.frame_window.window),
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

        diff = np.empty((len(self.frames), 3))

        for i, frame_index in enumerate(
            range(
                self.frames.index_start,
                self.frames.index_stop + 1,
                self.frames.index_step,
            )
        ):
            configuration = self.trajectory.configuration(frame_index)
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

        n_configs = self.frame_window.n_configs

        results = [correlate(diff, diff[:n_configs], mode="valid").T[0] / n_configs]
        for legendre_order in self.legendre_orders[1:]:
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
        for l_order, data in enumerate(x, 1):
            self._outputData[f"rtcf/l={l_order}"] += data

            if self.per_axis:
                self._outputData[f"rtcf/per_axis/l={l_order}"][index, :] = data

    def finalize(self):
        """Normalise and write out the results."""
        for l_order in self.legendre_orders:
            self._outputData[f"rtcf/l={l_order}"] /= self.n_molecules

        self._outputData.write(
            self.output_files.root,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
