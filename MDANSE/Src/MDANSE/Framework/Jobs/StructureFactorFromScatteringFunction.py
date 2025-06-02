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
from math import sqrt
import collections
import itertools as it

from MDANSE.Framework.Jobs.IJob import IJob


class StructureFactorFromScatteringFunction(IJob):
    """Computes the static structure factor from the intermediate
    scattering function from the dynamic coherent scattering function
    calculation results.
    """

    label = "Structure Factor From Scattering Function"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_data"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["dcsf_input_file"] = (
        "HDFInputFileConfigurator",
        {"label": "MDANSE Coherent Structure Factor", "default": "dcsf.mda"},
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
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        # The number of steps is set to 1 as everything is performed in the finalize method
        self.numberOfSteps = 1

        inputFile = self.configuration["dcsf_input_file"]["instance"]

        self._outputData.add("q", "LineOutputVariable", inputFile["q"][:], units="1/nm")
        nq = len(inputFile["q"][:])

        self._elementsPairs = sorted(
            it.combinations_with_replacement(
                self.configuration["atom_selection"]["unique_names"], 2
            )
        )
        for pair in self._elementsPairs:
            pair_str = "".join(map(str, pair))

            self._outputData.add(
                f"ssf_total_{pair_str}",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "ssf_total",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
            main_result=True,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
        """

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """Calculate the static structure factor from the intermediate
        scattering function.
        """
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        norm_natoms = 1.0 / sum(nAtomsPerElement.values())

        for pair in self._elementsPairs:
            pair_str = "".join(map(str, pair))
            fqt = self.configuration["dcsf_input_file"]["instance"][
                f"f(q,t)_{pair_str}"
            ]
            sqrt_cij = sqrt(
                nAtomsPerElement[pair[0]] * nAtomsPerElement[pair[1]] * norm_natoms**2
            )
            delta_ij = 1 if pair[0] == pair[1] else 0
            self._outputData[f"ssf_total_{pair_str}"][:] = (
                1 + (fqt[:, 0] - delta_ij) / sqrt_cij
            )
            self._outputData[f"ssf_total_{pair_str}"].scaling_factor = (
                fqt.attrs["scaling_factor"] * sqrt_cij
            )

            self._outputData["ssf_total"][:] += (
                self._outputData[f"ssf_total_{pair_str}"][:]
                * self._outputData[f"ssf_total_{pair_str}"].scaling_factor
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        self.configuration["dcsf_input_file"]["instance"].close()
        super().finalize()
