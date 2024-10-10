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

from MDANSE.Extensions import van_hove
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight


class VanHoveFunctionSelf(IJob):
    """The van Hove function is related to the intermediate scattering
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
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]
        self.n_configs = self.configuration["frames"]["n_configs"]
        self.n_frames = self.configuration["frames"]["n_frames"]

        self.selectedElements = self.configuration["atom_selection"]["unique_names"]
        self.nElements = len(self.selectedElements)

        self.n_mid_points = len(self.configuration["r_values"]["mid_points"])

        self._outputData.add(
            "r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "g(r,t)_total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.n_frames),
            axis="r|time",
            units="au",
        )
        self._outputData.add(
            "4_pi_r2_g(r,t)_total",
            "SurfaceOutputVariable",
            (self.n_mid_points, self.n_frames),
            axis="r|time",
            units="au",
        )
        for element in self.selectedElements:
            self._outputData.add(
                "g(r,t)_%s" % element,
                "SurfaceOutputVariable",
                (self.n_mid_points, self.n_frames),
                axis="r|time",
                units="au",
            )
            self._outputData.add(
                "4_pi_r2_g(r,t)_%s" % element,
                "SurfaceOutputVariable",
                (self.n_mid_points, self.n_frames),
                axis="r|time",
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
                - self.configuration["r_values"]["value"][i] ** 3
            )
        self.shell_volumes = (4 / 3) * np.pi * np.array(self.shell_volumes)

    def run_step(self, atm_index: int) -> tuple[int, tuple[np.ndarray, np.ndarray]]:
        """Calculates a distance histograms of an atoms displacement.
        The distance histograms are used to calculate the self part of
        the van Hove function.

        Parameters
        ----------
        atm_index : int
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

        idx = self.configuration["atom_selection"]["indexes"][atm_index][0]
        series = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
            idx,
            first=first,
            last=last,
            step=step,
        )
        cell_vols = np.array([
            self.configuration["trajectory"]["instance"].configuration(
                i
            ).unit_cell.volume for i in range(first, last, step)
        ])

        van_hove.van_hove_self(
            series,
            histograms,
            cell_vols,
            self.configuration["r_values"]["first"],
            self.configuration["r_values"]["step"],
            self.n_configs,
            self.n_frames,
        )

        return atm_index, histograms

    def combine(self, atm_index: int, histogram: np.ndarray):
        """Add the results into the histograms for the inputted time
        difference.

        Parameters
        ----------
        atm_index : int
            The atom index.
        histogram : np.ndarray
            A histogram of the distances between an atom at
            time t0 and t0 + t.
        """
        element = self.configuration["atom_selection"]["names"][atm_index]
        self._outputData["g(r,t)_{}".format(element)][:] += histogram
        self._outputData["4_pi_r2_g(r,t)_{}".format(element)][:] += histogram

    def finalize(self):
        """Using the distance histograms calculate, normalize and save the
        self part of the Van Hove function.
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["g(r,t)_%s" % element][:] /= (
                self.shell_volumes[:, np.newaxis] * number**2 * self.n_configs
            )
            self._outputData["4_pi_r2_g(r,t)_%s" % element][:] /= (
                number**2 * self.n_configs * self.configuration["r_values"]["step"]
            )

        weights = self.configuration["weights"].get_weights()
        self._outputData["g(r,t)_total"][:] = weight(
            weights,
            self._outputData,
            nAtomsPerElement,
            1,
            "g(r,t)_%s",
            update_partials=True,
        )
        self._outputData["4_pi_r2_g(r,t)_total"][:] = weight(
            weights,
            self._outputData,
            nAtomsPerElement,
            1,
            "4_pi_r2_g(r,t)_%s",
            update_partials=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )
        self.configuration["trajectory"]["instance"].close()
        super().finalize()
