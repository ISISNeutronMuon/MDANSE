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

from typing import TYPE_CHECKING

import numpy as np
from more_itertools import numeric_range

from MDANSE.Framework.AtomGrouping.grouping import add_grouped_totals
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    InstrumentResolution,
    MDANSETrajectory,
    OutputFile,
    Projection,
    QShellRange,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement

if TYPE_CHECKING:
    from collections.abc import Iterator


class GaussianDynamicIncoherentStructureFactor(IJob):
    r"""Computes the dynamic incoherent structure factor in the Gaussian approximation.

    Gaussian approximation is exact for a system of free particles and a system of
    particles undergoing brownian motion. The results of this analysis will be close
    to the Dynamic Incoherent Structure Factor analysis in the limits of very
    short :math:`\mathbf{q}` and very long :math:`\mathbf{q}`, and will differ from
    it for intermediate :math:`\mathbf{q}` values.
    """

    label = "Gaussian Dynamic Incoherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = ("instrument_resolution", "q_shells")

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
        grouping="grouping_level",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    q_shells = QShellRange(
        default=(0.0, 10.0, 1.0),
        minimum=0.0,
        include_last=False,
    )
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"}
    )
    projection = Projection()
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(default="b_incoherent", depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.resolution = self.instrument_resolution.run_resolution
        self.numberOfSteps = len(self.trajectory.atom_indices)

        self._nQShells = len(self.q_shells)
        self._nFrames = self.frame_window.n_frames
        self._nOmegas = self.resolution.n_omegas
        self._kSquare = np.array(self.q_shells) ** 2
        self.add_ideal_results = self.resolution.add_ideal
        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        self._outputData.add(
            "gdisf/axes/q",
            "LineOutputVariable",
            self.q_shells,
            units="1/nm",
        )

        self._outputData.add(
            "gdisf/axes/q2", "LineOutputVariable", self._kSquare, units="1/nm2"
        )

        self._outputData.add(
            "gdisf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )
        self._outputData.add(
            "gdisf/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window,
            units="au",
        )

        self._outputData.add(
            "gdisf/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )
        self._outputData.add(
            "gdisf/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
            axis="gdisf/axes/omega",
            units="au",
        )

        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"gdisf/f(q,t)/{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nFrames),
                axis="gdisf/axes/q|gdisf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"gdisf/s(q,f)/{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="gdisf/axes/q|gdisf/axes/omega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                f"msd/{element}",
                "LineOutputVariable",
                (self._nFrames,),
                axis="gdisf/axes/time",
                units="nm2",
            )
            if self.add_ideal_results:
                self._outputData.add(
                    f"gdisf/s(q,f)/ideal/{element}",
                    "SurfaceOutputVariable",
                    (self._nQShells, self._nOmegas),
                    axis="gdisf/axes/q|gdisf/axes/omega",
                    units="au",
                )

        self._outputData.add(
            "gdisf/f(q,t)/total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nFrames),
            axis="gdisf/axes/q|gdisf/axes/time",
            units="au",
        )
        self._outputData.add(
            "gdisf/s(q,f)/total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nOmegas),
            axis="gdisf/axes/q|gdisf/axes/omega",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "msd/total",
            "LineOutputVariable",
            (self._nFrames,),
            axis="gdisf/axes/time",
            units="nm2",
        )
        if self.add_ideal_results:
            self._outputData.add(
                "gdisf/s(q,f)/ideal/total",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="gdisf/axes/q|gdisf/axes/omega",
                units="au",
            )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index: int):
        """Calculates the GDISF and MSD of an atom.

        Parameters
        ----------
        index : int
            The index of the atom that the calculation will be run over.

        Returns
        -------
        tuple[int, tuple[np.ndarray, np.ndarray]]
            A tuple which contains the job index and a tuple of the
            GDISF and MSD of an atom.
        """

        # get atom index
        atom_index = self.trajectory.atom_indices[index]

        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.frames.index_start,
            last=self.frames.index_stop + 1,
            step=self.frames.index_step,
        )

        series = self.projection.projector(series)

        atomicSF = np.zeros((self._nQShells, self._nFrames), dtype=np.float64)

        msd = mean_square_displacement(series, self.frame_window.n_configs)

        for i, q2 in enumerate(self._kSquare):
            gaussian = np.exp(-msd * q2 / 6.0)
            atomicSF[i, :] += gaussian

        return index, (atomicSF, msd)

    def combine(self, index: int, x: tuple[np.ndarray, np.ndarray]):
        """Add the results to the output files.

        Parameters
        ----------
        index : int
            The atom index that the calculation was run over.
        x : tuple[np.ndarray, np.ndarray]
            A tuple of the GDISF and MSD of an atom.
        """
        element = self._atoms[self.trajectory.atom_indices[index]]
        atomicSF, msd = x
        self._outputData[f"gdisf/f(q,t)/{element}"] += atomicSF
        self._outputData[f"msd/{element}"] += msd

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"gdisf/f(q,t)/{element}"][:] /= number
            self._outputData[f"gdisf/s(q,f)/{element}"][:] = get_spectrum(
                self._outputData[f"gdisf/f(q,t)/{element}"],
                self.resolution.time_window,
                self.frames.time_step,
                axis=1,
            )
            self._outputData[f"msd/{element}"][:] /= number
            if self.add_ideal_results:
                self._outputData[f"gdisf/s(q,f)/ideal/{element}"][:] = get_spectrum(
                    self._outputData[f"gdisf/f(q,t)/{element}"],
                    None,
                    self.frames.time_step,
                    axis=1,
                )

        selected_weights, all_weights = self.trajectory.get_weights(prop=self.weights)
        for weights in selected_weights, all_weights:
            for key, value in weights.items():
                weights[key] = abs(value) ** 2
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "gdisf/f(q,t)/%s", self.labels)
        assign_weights(self._outputData, weight_dict, "gdisf/s(q,f)/%s", self.labels)
        if self.add_ideal_results:
            assign_weights(
                self._outputData, weight_dict, "gdisf/s(q,f)/ideal/%s", self.labels
            )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["gdisf/f(q,t)/total"][:] = (
            weighted_sum(self._outputData, "gdisf/f(q,t)/%s", self.labels)
        ) / fact
        self._outputData["gdisf/s(q,f)/total"][:] = (
            weighted_sum(self._outputData, "gdisf/s(q,f)/%s", self.labels)
        ) / fact
        self._outputData["gdisf/f(q,t)/total"].scaling_factor = fact
        self._outputData["gdisf/s(q,f)/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "gdisf/f(q,t)",
            "SurfaceOutputVariable",
            axis="gdisf/axes/q|gdisf/axes/time",
            units="au",
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "gdisf/s(q,f)",
            "SurfaceOutputVariable",
            axis="gdisf/axes/q|gdisf/axes/omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.add_ideal_results:
            self._outputData["gdisf/s(q,f)/ideal/total"][:] = (
                weighted_sum(self._outputData, "gdisf/s(q,f)/ideal/%s", self.labels)
                / fact
            )
            self._outputData["gdisf/s(q,f)/ideal/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                "gdisf/s(q,f)/ideal",
                "SurfaceOutputVariable",
                axis="gdisf/axes/q|gdisf/axes/omega",
                units="au",
            )

        # since GDISF ~ exp(-msd * q2 / 6.0) the MSD isn't weighted in
        # the exp lets save the MSD with equal weights
        selected_weights, all_weights = self.trajectory.get_weights(prop="equal")
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            1,
        )

        assign_weights(self._outputData, weight_dict, "msd/%s", self.labels)
        self._outputData["msd/total"][:] = (
            weighted_sum(self._outputData, "msd/%s", self.labels) / fact
        )

        self._outputData["msd/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "msd",
            "LineOutputVariable",
            axis="gdisf/axes/time",
            units="nm2",
        )

        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
