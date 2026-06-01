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
import numpy.typing as npt

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    FrameSelect,
    GridStep,
    MDANSETrajectory,
    OutputFile,
    RunningMode,
)


class MolecularTrace(IJob):
    """Maps the volume occupied by atoms over time.

    A Molecular Trace is a time-integrated trace of selected atoms coordinates.

    * the minimal and maximal coordinates from the selected atomic trajectories are
      computed.
    * based on these min/max and a spatial resolution, a cartesian grid is constructed.
    * for each atom and for each frame of the selected trajectories, a histogram of
      presence, called the spatial density, is constructed.

    The molecular trace can reveal anisotropic vibrations and diffusion pathways.

    **Acknowledgement and publication:**
    Gael Goret, PELLEGRINI Eric
    """

    label = "Molecular Trace"

    category = (
        "Analysis",
        "Structure",
    )
    PREDICTORS = ("spatial_resolution",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    spatial_resolution = GridStep(
        minimum=0.0,
        default=0.1,
        depends={"frames": "frames", "trajectory": "trajectory"},
    )
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        super().initialize()

        self.numberOfSteps = len(self.frames)

        # Generate the grids that will be used to quantify the presence of atoms in an area.

        self.min = np.full(3, np.inf, dtype=np.float64)
        self.max = np.full(3, -np.inf, dtype=np.float64)
        for frame_index in self.frames.indices:
            conf = self.trajectory.configuration(frame_index)
            conf = conf.continuous_configuration()
            coords = conf["coordinates"]

            self.min = np.minimum(self.min, coords.min(axis=0))
            self.max = np.maximum(self.max, coords.max(axis=0))

        dim = self.max - self.min

        self._outputData.add("origin", "LineOutputVariable", self.min, units="nm")

        self.gdim = np.ceil(dim / self.spatial_resolution).astype(int)

        self._outputData.add(
            "spacing",
            "LineOutputVariable",
            np.array([self.spatial_resolution] * 3),
            units="nm",
        )

        self.grid = np.zeros(self.gdim, dtype=np.int32)

        labels = ["x_position", "y_position", "z_position"]
        for label, gdim, mini in zip(labels, self.gdim, self.min, strict=True):
            self._outputData.add(
                label,
                "LineOutputVariable",
                np.arange(0, gdim, 1) * self.spatial_resolution + mini,
                units="nm",
            )

        self._outputData.add(
            "molecular_trace",
            "VolumeOutputVariable",
            tuple(self.gdim),
            axis="|".join(labels),
            main_result=True,
        )

        self._indices = self.trajectory.atom_indices

    def run_step(self, index: int) -> npt.NDArray[int]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int.
            the index of the step.

        Returns
        -------
        numpy.ndarray
            Grid trace.
        """

        # This is the actual index of the frame corresponding to the loop index.
        frame = self.frames[index]

        conf = self.trajectory.configuration(frame.ind)
        conf = conf.continuous_configuration()

        grid = np.zeros(self.gdim, dtype=np.int32)

        indices = np.floor(
            (conf["coordinates"][self._indices, :] - self.min.reshape((1, 3)))
            / self.spatial_resolution
        ).astype(int)
        unique_indices, counts = np.unique(indices, return_counts=True, axis=0)
        grid[tuple(unique_indices.T)] += counts

        return index, grid

    def combine(self, index: int, grid: npt.NDArray[int]) -> None:
        """

        Parameters
        ----------
        index : int.
            The index of the step.
        x : ~numpy.ndarray
            The output of run_step method.

        Returns
        -------

        """
        self.grid += grid

    def finalize(self):
        """
        Finalize the job.
        """

        self._outputData["molecular_trace"][:] = self.grid

        # Write the output variables.
        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
