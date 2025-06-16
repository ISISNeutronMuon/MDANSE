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

import numpy as np
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


class ScatteringLengthDensityProfileError(Error):
    pass


class ScatteringLengthDensityProfile(IJob):
    """Produces the time-averaged scattering length density profile.

    The result can be used in neutron reflectometry calculations.
    """

    label = "Scattering Length Density Profile"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["axis"] = (
        "SingleChoiceConfigurator",
        {"choices": ["a", "b", "c"], "default": "c"},
    )
    settings["dr"] = ("FloatConfigurator", {"default": 0.01, "mini": 1.0e-9})
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["frames"]["number"]

        self._dr = self.configuration["dr"]["value"]

        self.axis_index = self.configuration["axis"]["index"]
        trajectory = self.configuration["trajectory"]["instance"]
        first_conf = self.configuration["trajectory"]["instance"].configuration()

        try:
            axis = first_conf.unit_cell.direct[self.axis_index, :]
        except Exception:
            raise ScatteringLengthDensityProfileError(
                "Density profile cannot be computed without a simulation box. "
                "You can add a box using TrajectoryEditor."
            )

        axis_length = np.sqrt(np.sum(axis**2))
        self._n_bins = int(axis_length / self._dr) + 1

        self._outputData.add("r", "LineOutputVariable", (self._n_bins,), units="nm")

        self._indices_per_element = self.configuration["atom_selection"].get_indices()
        self._elements = list(self.configuration["atom_selection"].get_natoms().keys())

        self.scattering_lengths = {
            element: [
                trajectory.get_atom_property(element, "b_coherent"),
                trajectory.get_atom_property(element, "b_incoherent"),
                np.sqrt(trajectory.get_atom_property(element, "xs_scattering"))
                / (4 * np.pi),
            ]
            for element in self._elements
        }

        for element in self._elements:
            self._outputData.add(
                f"dp_{element}",
                "LineOutputVariable",
                (self._n_bins,),
                axis="r",
                units="1 / ang3",
                main_result=True,
            )

        for component in ["coherent", "incoherent", "total"]:
            self._outputData.add(
                f"sldp_{component}",
                "LineOutputVariable",
                (self._n_bins,),
                axis="r",
                units="1e-6 / ang2",
                main_result=True,
            )

        self._extent = 0.0

    def run_step(self, index: int):
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            The index of the step.

        Returns
        -------
        int
            Index calculated.
        tuple[float, np.ndarray]
            Axis length and density profile.
        """

        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)

        box_coords = conf.to_box_coordinates()
        box_coords = box_coords - np.floor(box_coords)

        axis_index = self.configuration["axis"]["index"]
        axis = conf.unit_cell.direct[axis_index, :]
        axis_length = np.sqrt(np.sum(axis**2))
        self._extent += axis_length

        slice_volume = conf.unit_cell.volume / self._n_bins

        dp_per_frame = {}

        for element, indices in self._indices_per_element.items():
            dp_per_frame[element], _bins = np.histogram(
                box_coords[indices, axis_index],
                bins=self._n_bins,
                range=(0.0, 1.0),
            )

        return index, (slice_volume, dp_per_frame)

    def combine(self, index: int, data: tuple[float, dict[str, np.ndarray]]) -> None:
        """Combine results together.

        Parameters
        ----------
        index : int
            The index of the step.
        data : tuple[float, dict[str, np.ndarray]]
            Axis length and density profile.
        """

        slice_volume, density_profile = data

        for element, hist in density_profile.items():
            self._outputData[f"dp_{element}"] += hist / slice_volume
            slen_dict = self.scattering_lengths[element]
            for nb, component in enumerate(["coherent", "incoherent", "total"]):
                self._outputData[f"sldp_{component}"] += (
                    slen_dict[element][nb] * hist / slice_volume
                )

    def finalize(self) -> None:
        """
        Finalize the job.
        """

        self._extent /= self.numberOfSteps

        r_values = np.linspace(0, self._extent, self._n_bins + 1)
        self._outputData["r"][:] = (r_values[1:] + r_values[:-1]) / 2

        for element in self._elements:
            self._outputData[f"dp_{element}"] /= self.numberOfSteps

        for component in ["coherent", "incoherent", "total"]:
            self._outputData[f"sldp_{component}"] /= self.numberOfSteps

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
