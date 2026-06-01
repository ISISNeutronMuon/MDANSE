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

from MDANSE.Framework.AtomGrouping.grouping import add_grouped_totals
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    FrameSelect,
    GroupingLevel,
    MDANSETrajectory,
    OutputFile,
    Projection,
    QVectors,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


class ElasticIncoherentStructureFactor(IJob):
    """Calculates the Elastic Incoherent Structure Factor of a trajectory.

    The Elastic Incoherent Structure Factor (EISF) is defined as the limit of the
    incoherent intermediate scattering function for infinite time.

    The EISF appears as the incoherent amplitude of the elastic line in the neutron
    scattering spectrum. Elastic scattering is only present for systems in which
    the atomic motion is confined in space, as in solids. The Q-dependence of the
    EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence
    of the dynamics.
    """

    label = "Elastic Incoherent Structure Factor"

    # The category of the analysis.
    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = ("q_vectors",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
        grouping="grouping_level",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    q_vectors = QVectors(depends={"trajectory": "trajectory"})
    projection = Projection()
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(
        default="b_incoherent",
        depends={
            "trajectory": "trajectory",
        },
    )
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.generator = self.q_vectors.generator
        self.numberOfSteps = len(self.trajectory.atom_indices)

        self._nQShells = self.generator.n_shells

        self._nFrames = len(self.frames)

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        self._outputData.add(
            "eisf/axes/q",
            "LineOutputVariable",
            self.generator.shells,
            units="1/nm",
        )

        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"eisf/{element}",
                "LineOutputVariable",
                (self._nQShells,),
                axis="eisf/axes/q",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "eisf/total",
            "LineOutputVariable",
            (self._nQShells,),
            axis="eisf/axes/q",
            units="au",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index: int) -> tuple[int, np.NDArray[float]]:
        """
        Runs a single step of the job.

        Parameters
        ----------
        index : int
            The index of the step.

        Returns
        -------
        index : int
            The index of the step.
        atomicEISF : np.array
            The atomic elastic incoherent structure factor.
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

        atomicEISF = np.zeros((self._nQShells,), dtype=np.float64)

        for i, q in enumerate(self.generator.shells):
            if q not in self.generator.q_vectors or self.generator.q_vectors[q] is None:
                continue

            qVectors = self.generator.q_vectors[q]["q_vectors"]

            a = np.average(np.exp(1j * np.dot(series, qVectors)), axis=0)
            a = np.abs(a) ** 2

            atomicEISF[i] = np.average(a)

        return index, atomicEISF

    def combine(self, index, x):
        """
        Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The index of the step.
        x : Any
            The returned result(s) of run_step.
        """

        # The symbol of the atom.
        element = self._atoms[self.trajectory.atom_indices[index]]

        self._outputData[f"eisf/{element}"] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        self.generator.write_vectors_to_file(self._outputData)

        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"eisf/{element}"][:] /= number

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
        assign_weights(self._outputData, weight_dict, "eisf/%s", self.labels)

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["eisf/total"][:] = (
            weighted_sum(self._outputData, "eisf/%s", self.labels) / fact
        )
        self._outputData["eisf/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "eisf",
            "LineOutputVariable",
            axis="eisf/axes/q",
            units="au",
            main_result=True,
            partial_result=True,
        )

        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
