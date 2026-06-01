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
import itertools as it
from math import sqrt

from MDANSE.Framework.AtomGrouping.grouping import add_grouped_totals, pair_labels
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    GroupingLevel,
    MDANSEResult,
    MDANSETrajectory,
    OutputFile,
)


class StructureFactorFromScatteringFunction(IJob):
    """Computes the static structure factor from the results of another analysis.

    The static structure factor is calculated from the intermediate
    scattering function of the dynamic coherent scattering function
    calculation results.

    Parameters
    ----------

    Returns
    -------

    """

    label = "Structure Factor From Scattering Function"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_data"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
        grouping="grouping_level",
    )
    dcsf_input_file = MDANSEResult(
        tooltip="Input MDANSE result containing DCSF result.",
        label="MDANSE Coherent Structure Factor",
        choices=("dcsf",),
    )
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    output_files = OutputFile()

    def initialize(self):
        """Initialize the input parameters and analysis self variables"""
        super().initialize()

        # The number of steps is set to 1 as everything is performed in the finalize method
        self.numberOfSteps = 1

        inputFile = self.dcsf_input_file

        self._outputData.add(
            "ssf/axes/q",
            "LineOutputVariable",
            inputFile["dcsf/axes/q"][:],
            units="1/nm",
        )
        nq = len(inputFile["dcsf/axes/q"][:])
        self.labels = pair_labels(
            self.trajectory,
        )

        for pair_str, _ in self.labels:
            self._outputData.add(
                f"ssf/{pair_str}",
                "LineOutputVariable",
                (nq,),
                axis="ssf/axes/q",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "ssf/total",
            "LineOutputVariable",
            (nq,),
            axis="ssf/axes/q",
            units="au",
            main_result=True,
        )

    def run_step(self, index: int) -> tuple[int, None]:
        """Dummy run step.

        Parameters
        ----------
        index : int
            Index of current step.

        Returns
        -------
        tuple[int, None]
            Index of current step.
        """

        return index, None

    def combine(self, _index, _x):
        """Dummy combine step.

        Parameters
        ----------
        _index : int
            Unused.
        _x : None
            Unused.
        """

    def finalize(self):
        """Calculate the static structure factor from the intermediate
        scattering function.
        """
        nAtomsPerElement = self.trajectory.get_natoms()
        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = (n_selected / n_total) ** 2
        norm_natoms = 1.0 / n_total

        for pair_str, (label_i, label_j) in self.labels:
            fqt = self.dcsf_input_file[f"dcsf/f(q,t)/{pair_str}"]
            sqrt_cij = sqrt(
                nAtomsPerElement[label_i] * nAtomsPerElement[label_j] * norm_natoms**2
            )
            delta_ij = 1 if label_i == label_j else 0
            self._outputData[f"ssf/{pair_str}"][:] = (
                1 + (fqt[:, 0] - delta_ij) / sqrt_cij
            )
            self._outputData[f"ssf/{pair_str}"].scaling_factor = (
                fqt.attrs["scaling_factor"] * sqrt_cij
            )

            self._outputData["ssf/total"][:] += (
                self._outputData[f"ssf/{pair_str}"][:]
                * self._outputData[f"ssf/{pair_str}"].scaling_factor
                / fact
            )

        self._outputData["ssf/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ssf",
            "LineOutputVariable",
            dim=2,
            axis="ssf/axes/q",
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
        self.dcsf_input_file.close()
        super().finalize()
