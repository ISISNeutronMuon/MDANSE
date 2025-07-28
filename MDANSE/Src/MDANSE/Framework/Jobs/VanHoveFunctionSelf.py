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

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.VanHoveFunctionDistinct import (
    CELL_SIZE_LIMIT,
    DETAILED_CELL_MESSAGE,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


def van_hove_self(
    xyz: np.ndarray,
    histograms: np.ndarray,
    cell_vols: np.ndarray,
    rmin: float,
    dr: float,
    n_configs: int,
    n_frames: int,
):
    """Calculate the self van Hove function for one atom.

    Calculates the distance histogram between an atom at time t0
    and the same atom at a time t0 + t. The results from this function
    can be used to calculate the self part of the van Hove function.

    Parameters
    ----------
    xyz : np.ndarray
        The trajectory of an atom.
    histograms : np.ndarray
        The histograms to be updated.
    cell_vols : np.ndarray
        The cell volumes.
    rmin : float
        The minimum distance of the histogram.
    dr : float
        The distances between histogram bins.
    n_configs : int
        Number of configs to be averaged over.
    n_frames : int
        Number of correlation frames.

    """
    nbins = histograms.shape[0]

    for i in range(n_configs):
        x0 = xyz[i]
        r_array = xyz[i : i + n_frames] - x0.reshape((1, 3))
        distance_array = np.sqrt((r_array**2).sum(axis=1))
        bins = ((distance_array - rmin) / dr).astype(int)
        valid_bins = np.logical_and(bins >= 0, bins < nbins)
        for j in range(n_frames):
            if valid_bins[j]:
                histograms[bins[j], j] += cell_vols[i + j]
    return histograms


class VanHoveFunctionSelf(IJob):
    """Calculates the self part of the van Hove function.

    The van Hove function is related to the intermediate scattering
    function via a Fourier transform and the dynamic structure factor
    via a double Fourier transform. The van Hove function describes the
    probability of finding a particle (j) at a distance r at time t from
    a particle (i) at a time t_0. The van Hove function can be split
    into self and distinct parts. The self part includes only the
    contributions from only the same particles (i=j) while the distinct
    part includes only the contributions between different particles
    (i≠j). This job calculates a self part of the van Hove function.
    """

    label = "Van Hove Function Self"

    enabled = True

    category = (
        "Analysis",
        "Dynamics",
    )

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["r_values"] = (
        "DistHistCutoffConfigurator",
        {
            "label": "r values (nm)",
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "dependencies": {"trajectory": "trajectory"},
            "max_value": False,
        },
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)
        self.n_configs = self.configuration["frames"]["n_configs"]
        self.n_frames = self.configuration["frames"]["n_frames"]
        self._atoms = self.trajectory.atom_names

        self.selectedElements = self.trajectory.unique_names
        self.nElements = len(self.selectedElements)

        self.n_mid_points = len(self.configuration["r_values"]["mid_points"])

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        conf = self.trajectory.configuration(
            self.configuration["frames"]["first"],
        )
        if not hasattr(conf, "unit_cell"):
            raise ValueError(DETAILED_CELL_MESSAGE)
        if conf.unit_cell.volume < CELL_SIZE_LIMIT:
            raise ValueError(DETAILED_CELL_MESSAGE)

        self._outputData.add(
            "vh/axes/r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )
        self._outputData.add(
            "vh/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "vh/g(r,t)/total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.n_frames),
            axis="vh/axes/r|vh/axes/time",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "vh/4_pi_r2_g(r,t)/total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.n_frames),
            axis="vh/axes/r|vh/axes/time",
            units="au",
        )
        for element in self.selectedElements:
            self._outputData.add(
                f"vh/g(r,t)/{element}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.n_frames),
                axis="vh/axes/r|vh/axes/time",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                f"vh/4_pi_r2_g(r,t)/{element}",
                "SurfaceOutputVariable",
                (self.n_mid_points, self.n_frames),
                axis="vh/axes/r|vh/axes/time",
                units="au",
            )

        # usually the normalization is 4 * pi * r^2 * dr which is
        # correct for small values of dr or large values of r.
        # unlike the PDF, g(r, t) may not be zero around r=0 we will use
        # the actual shell volume instead.
        self.shell_volumes = []
        for i in range(self.n_mid_points):
            self.shell_volumes.append(
                (
                    self.configuration["r_values"]["value"][i]
                    + self.configuration["r_values"]["step"]
                )
                ** 3
                - self.configuration["r_values"]["value"][i] ** 3,
            )
        self.shell_volumes = (4 / 3) * np.pi * np.array(self.shell_volumes)

    def run_step(self, index: int) -> tuple[int, tuple[np.ndarray, np.ndarray]]:
        """Run the analysis for a single atom.

        Calculates a distance histograms of an atoms displacement.
        The distance histograms are used to calculate the self part of
        the van Hove function.

        Parameters
        ----------
        index : int
            The index of the atom which will be used to generate the
            distance histograms.

        Returns
        -------
        tuple
            A tuple containing the atom index and distance histograms.

        """
        histograms = np.zeros((self.n_mid_points, self.n_frames))
        first = self.configuration["frames"]["first"]
        last = self.configuration["frames"]["last"] + 1
        step = self.configuration["frames"]["step"]

        atom_index = self.trajectory.atom_indices[index]
        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=first,
            last=last,
            step=step,
        )
        cell_vols = np.array(
            [
                self.trajectory.configuration(i).unit_cell.volume
                for i in range(first, last, step)
            ],
        )

        histograms = van_hove_self(
            series,
            histograms,
            cell_vols,
            self.configuration["r_values"]["first"],
            self.configuration["r_values"]["step"],
            self.n_configs,
            self.n_frames,
        )

        return index, histograms

    def combine(self, index: int, histogram: np.ndarray):
        """Add the results into the histograms for the input time difference.

        Parameters
        ----------
        index : int
            The atom index.
        histogram : np.ndarray
            A histogram of the distances between an atom at
            time t0 and t0 + t.

        """
        element = self._atoms[self.trajectory.atom_indices[index]]
        self._outputData[f"vh/g(r,t)/{element}"][:] += histogram
        self._outputData[f"vh/4_pi_r2_g(r,t)/{element}"][:] += histogram

    def finalize(self):
        """Apply scaling to the summed up results.

        Using the distance histograms calculate, normalize and save the
        self part of the Van Hove function.
        """
        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"vh/g(r,t)/{element}"][:] /= (
                self.shell_volumes[:, np.newaxis] * number**2 * self.n_configs
            )
            self._outputData[f"vh/4_pi_r2_g(r,t)/{element}"][:] /= (
                number**2 * self.n_configs * self.configuration["r_values"]["step"]
            )

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        for weights in selected_weights, all_weights:
            for key, value in weights.items():
                weights[key] = value**2
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "vh/g(r,t)/%s", self.labels)
        assign_weights(
            self._outputData, weight_dict, "vh/4_pi_r2_g(r,t)/%s", self.labels
        )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["vh/g(r,t)/total"][:] = (
            weighted_sum(self._outputData, "vh/g(r,t)/%s", self.labels) / fact
        )
        self._outputData["vh/g(r,t)/total"].scaling_factor = fact
        self._outputData["vh/4_pi_r2_g(r,t)/total"][:] = (
            weighted_sum(self._outputData, "vh/4_pi_r2_g(r,t)/%s", self.labels) / fact
        )
        self._outputData["vh/4_pi_r2_g(r,t)/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "vh/g(r,t)",
            "SurfaceOutputVariable",
            axis="vh/axes/r|vh/axes/time",
            units="au",
            main_result=True,
            partial_result=True,
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "vh/4_pi_r2_g(r,t)",
            "SurfaceOutputVariable",
            axis="vh/axes/r|vh/axes/time",
            units="au",
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self.trajectory.close()
        super().finalize()
