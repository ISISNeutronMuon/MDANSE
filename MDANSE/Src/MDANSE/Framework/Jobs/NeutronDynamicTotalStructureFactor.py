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
import itertools
from math import sqrt

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob


class NeutronDynamicTotalStructureFactorError(Error):
    pass


class NeutronDynamicTotalStructureFactor(IJob):
    """
    Computes the dynamic total structure factor for a set of atoms as the sum of the incoherent and coherent structure factors
    """

    enabled = True

    label = "Neutron Dynamic Total Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["dcsf_input_file"] = (
        "HDFInputFileConfigurator",
        {"label": "MDANSE Coherent Structure Factor", "default": "dcsf.mda"},
    )
    settings["disf_input_file"] = (
        "HDFInputFileConfigurator",
        {"label": "MDANSE Incoherent Structure Factor", "default": "disf.mda"},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
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
                "atom_selection": "atom_selection",
                "grouping_level": "grouping_level",
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = 1

        self.pair_labels = self.configuration["grouping_level"].pair_labels()

        # Check time consistency
        if "time" not in self.configuration["dcsf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No time found in dcsf input file"
            )
        if "time" not in self.configuration["disf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No time found in disf input file"
            )

        dcsf_time = self.configuration["dcsf_input_file"]["instance"]["time"][:]
        disf_time = self.configuration["disf_input_file"]["instance"]["time"][:]

        if not np.all(dcsf_time == disf_time):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent times between dcsf and disf input files"
            )

        self._outputData.add("time", "LineOutputVariable", dcsf_time, units="ps")

        # Check time window consistency
        if "time_window" not in self.configuration["dcsf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No time window found in dcsf input file"
            )
        if "time_window" not in self.configuration["disf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No time window found in disf input file"
            )

        dcsf_time_window = self.configuration["dcsf_input_file"]["instance"][
            "time_window"
        ][:]
        disf_time_window = self.configuration["disf_input_file"]["instance"][
            "time_window"
        ][:]

        if not np.all(dcsf_time_window == disf_time_window):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent time windows between dcsf and disf input files"
            )

        self._outputData.add(
            "time_window", "LineOutputVariable", dcsf_time_window, units="au"
        )

        # Check q values consistency
        if "q" not in self.configuration["dcsf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No q values found in dcsf input file"
            )
        if "q" not in self.configuration["disf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No q values found in disf input file"
            )

        dcsf_q = self.configuration["dcsf_input_file"]["instance"]["q"][:]
        disf_q = self.configuration["disf_input_file"]["instance"]["q"][:]

        if not np.all(dcsf_q == disf_q):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent q values between dcsf and disf input files"
            )

        self._outputData.add("q", "LineOutputVariable", dcsf_q, units="1/nm")

        # Check omega consistency
        if "omega" not in self.configuration["dcsf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No omega found in dcsf input file"
            )
        if "omega" not in self.configuration["disf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No omega found in disf input file"
            )

        dcsf_omegas = self.configuration["dcsf_input_file"]["instance"]["omega"][:]
        disf_omegas = self.configuration["disf_input_file"]["instance"]["omega"][:]

        if not np.all(dcsf_omegas == disf_omegas):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent omegas between dcsf and disf input files"
            )

        self._outputData.add("omega", "LineOutputVariable", dcsf_omegas, units="rad/ps")

        # Check omega window consistency
        if "omega_window" not in self.configuration["dcsf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No omega window found in dcsf input file"
            )
        if "omega_window" not in self.configuration["disf_input_file"]["instance"]:
            raise NeutronDynamicTotalStructureFactorError(
                "No omega window found in disf input file"
            )

        dcsf_omega_window = self.configuration["dcsf_input_file"]["instance"][
            "omega_window"
        ][:]
        disf_omega_window = self.configuration["disf_input_file"]["instance"][
            "omega_window"
        ][:]

        if not np.all(dcsf_omega_window == disf_omega_window):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent omega windows between dcsf and disf input files"
            )

        self._outputData.add(
            "omega_window", "LineOutputVariable", dcsf_omegas, units="au"
        )

        # Check f(q,t) and s(q,f) for dcsf
        for pair_str, _ in self.pair_labels:
            if (
                f"f(q,t)_{pair_str}"
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in dcsf input file"
                )
            if (
                f"s(q,f)_{pair_str}"
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in dcsf input file"
                )
            if (
                "scaling_factor"
                not in self.configuration["dcsf_input_file"]["instance"][
                    f"s(q,f)_{pair_str}"
                ].attrs.keys()
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "This DCSF file was created before the new scaling scheme. Please calculate it again."
                )

        for element in self.configuration["atom_selection"]["unique_names"]:
            if (
                f"f(q,t)_{element}"
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in disf input file"
                )
            if (
                f"s(q,f)_{element}"
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in disf input file"
                )
            if (
                "scaling_factor"
                not in self.configuration["disf_input_file"]["instance"][
                    f"s(q,f)_{element}"
                ].attrs.keys()
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "This DISF file was created before the new scaling scheme. Please calculate it again."
                )

        for element in self.configuration["atom_selection"]["unique_names"]:
            fqt = self.configuration["disf_input_file"]["instance"][f"f(q,t)_{element}"]
            sqf = self.configuration["disf_input_file"]["instance"][f"s(q,f)_{element}"]
            self._outputData.add(
                f"f(q,t)_inc_{element}",
                "SurfaceOutputVariable",
                fqt,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                f"s(q,f)_inc_{element}",
                "SurfaceOutputVariable",
                sqf,
                axis="q|omega",
                units="nm2/ps",
            )

        for pair_str, _ in self.pair_labels:
            fqt = self.configuration["dcsf_input_file"]["instance"][
                f"f(q,t)_{pair_str}"
            ]
            sqf = self.configuration["dcsf_input_file"]["instance"][
                f"s(q,f)_{pair_str}"
            ]
            self._outputData.add(
                f"f(q,t)_coh_{pair_str}",
                "SurfaceOutputVariable",
                fqt,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                f"s(q,f)_coh_{pair_str}",
                "SurfaceOutputVariable",
                sqf,
                axis="q|omega",
                units="nm2/ps",
            )

        nQValues = len(dcsf_q)
        nTimes = len(dcsf_time)
        nOmegas = len(dcsf_omegas)

        self._outputData.add(
            "f(q,t)_coh_total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "f(q,t)_inc_total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "f(q,t)_total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="q|time",
            units="au",
        )

        self._outputData.add(
            "s(q,f)_coh_total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="q|omega",
            units="nm2/ps",
            main_result=True,
            partial_result=True,
        )
        self._outputData.add(
            "s(q,f)_inc_total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="q|omega",
            units="nm2/ps",
            main_result=True,
            partial_result=True,
        )
        self._outputData.add(
            "s(q,f)_total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="q|omega",
            units="nm2/ps",
            main_result=True,
        )
        self._input_disf_weight = (
            self.configuration["disf_input_file"]["instance"][
                "metadata/inputs/weights"
            ][0]
            .decode()
            .strip('"')
        )
        self._input_dcsf_weight = (
            self.configuration["dcsf_input_file"]["instance"][
                "metadata/inputs/weights"
            ][0]
            .decode()
            .strip('"')
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. rho (np.array): The exponential part of I(k,t)
        """

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.configuration["atom_selection"].get_all_natoms().values())
        fact = n_selected / n_total

        norm_natoms = 1.0 / n_total
        # Compute coherent functions and structure factor
        for pair_str, (label_i, label_j) in self.pair_labels:
            ele_i = self.configuration["grouping_level"].get_element_from_label(label_i)
            ele_j = self.configuration["grouping_level"].get_element_from_label(label_j)
            bi = self.configuration["trajectory"]["instance"].get_atom_property(
                ele_i, "b_coherent"
            )
            bj = self.configuration["trajectory"]["instance"].get_atom_property(
                ele_j, "b_coherent"
            )
            sqrt_cij = sqrt(
                nAtomsPerElement[label_i] * nAtomsPerElement[label_j] * norm_natoms**2
            )
            pre_fac = 1 if label_i == label_j else 2
            self._outputData[f"f(q,t)_coh_{pair_str}"].scaling_factor *= (
                pre_fac * bi * bj * sqrt_cij
            )
            self._outputData[f"s(q,f)_coh_{pair_str}"].scaling_factor *= (
                pre_fac * bi * bj * sqrt_cij
            )

            self._outputData["f(q,t)_coh_total"][:] += (
                self._outputData[f"f(q,t)_coh_{pair_str}"][:]
                * self._outputData[f"f(q,t)_coh_{pair_str}"].scaling_factor
                / fact
            )
            self._outputData["s(q,f)_coh_total"][:] += (
                self._outputData[f"s(q,f)_coh_{pair_str}"][:]
                * self._outputData[f"s(q,f)_coh_{pair_str}"].scaling_factor
                / fact
            )

        self._outputData["f(q,t)_coh_total"].scaling_factor = fact
        self._outputData["s(q,f)_coh_total"].scaling_factor = fact

        # Compute incoherent functions and structure factor
        for label, number in nAtomsPerElement.items():
            ele_i = self.configuration["grouping_level"].get_element_from_label(label)
            bi = self.configuration["trajectory"]["instance"].get_atom_property(
                ele_i, "b_incoherent2"
            )
            self._outputData[f"f(q,t)_inc_{label}"].scaling_factor *= (
                bi * number * norm_natoms
            )
            self._outputData[f"s(q,f)_inc_{label}"].scaling_factor *= (
                bi * number * norm_natoms
            )
            self._outputData["f(q,t)_inc_total"][:] += (
                self._outputData[f"f(q,t)_inc_{label}"][:]
                * self._outputData[f"f(q,t)_inc_{label}"].scaling_factor
                / fact
            )
            self._outputData["s(q,f)_inc_total"][:] += (
                self._outputData[f"s(q,f)_inc_{label}"][:]
                * self._outputData[f"s(q,f)_inc_{label}"].scaling_factor
                / fact
            )

        self._outputData["f(q,t)_inc_total"].scaling_factor = fact
        self._outputData["s(q,f)_inc_total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "f(q,t)_inc",
            "SurfaceOutputVariable",
            axis="q|time",
            units="au",
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "f(q,t)_coh",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="q|time",
            units="au",
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "s(q,f)_inc",
            "SurfaceOutputVariable",
            axis="q|omega",
            units="au",
            main_result=True,
            partial_result=True,
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "s(q,f)_coh",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="q|omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        # Compute total F(Q,t) = inc + coh
        self._outputData["f(q,t)_total"][:] = (
            self._outputData["f(q,t)_coh_total"][:]
            + self._outputData["f(q,t)_inc_total"][:]
        )
        self._outputData["f(q,t)_total"].scaling_factor = fact
        self._outputData["s(q,f)_total"][:] = (
            self._outputData["s(q,f)_coh_total"][:]
            + self._outputData["s(q,f)_inc_total"][:]
        )
        self._outputData["s(q,f)_total"].scaling_factor = fact

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self.configuration["trajectory"]["instance"].close()
        self.configuration["disf_input_file"]["instance"].close()
        self.configuration["dcsf_input_file"]["instance"].close()
        super().finalize()
