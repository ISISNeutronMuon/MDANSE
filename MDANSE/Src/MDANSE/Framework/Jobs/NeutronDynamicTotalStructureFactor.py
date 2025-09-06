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
import itertools
from math import sqrt

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    pair_labels,
)
from MDANSE.Framework.Jobs.IJob import IJob


class NeutronDynamicTotalStructureFactorError(Error):
    pass


class NeutronDynamicTotalStructureFactor(IJob):
    r"""Combines the coherent and incoherent dynamic structure factors.

    The partial results need to be calculated before using the Dynamic
    Coherent/Incoherent Structure Factor jobs with the same
    :math:`\mathbf{q}`-vector settings.

    The partial results will be scaled by neutron scattering lengths, producing
    a total result with coherent and incoherent parts on the same scale,
    directly comparable to each other.
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
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def _get_data_from_files(self, props: str):
        out = {}
        for file, prop in zip(("dcsf", "disf"), self._expand(props)):
            try:
                out[file] = self.configuration[f"{file}_input_file"]["instance"][prop][
                    :
                ]
            except KeyError:
                raise NeutronDynamicTotalStructureFactorError(
                    f"No `{prop}` found in {file} input file"
                )
        return tuple(out.values())

    @staticmethod
    def _expand(string: str):
        return "dcsf/" + string, "disf/" + string

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = 1

        self.pair_labels = pair_labels(
            self.trajectory,
        )

        # Check time consistency
        dcsf_time, disf_time = self._get_data_from_files("axes/time")

        if not np.all(dcsf_time == disf_time):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent times between dcsf and disf input files"
            )

        self._outputData.add(
            "ndsf/axes/time", "LineOutputVariable", dcsf_time, units="ps"
        )

        # Check time window consistency
        dcsf_time_window, disf_time_window = self._get_data_from_files(
            "res/time_window"
        )

        if not np.all(dcsf_time_window == disf_time_window):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent time windows between dcsf and disf input files"
            )

        self._outputData.add(
            "ndsf/axes/time_window", "LineOutputVariable", dcsf_time_window, units="au"
        )

        # Check q values consistency
        dcsf_q, disf_q = self._get_data_from_files("axes/q")

        if not np.all(dcsf_q == disf_q):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent q values between dcsf and disf input files"
            )

        self._outputData.add("ndsf/axes/q", "LineOutputVariable", dcsf_q, units="1/nm")

        # Check omega consistency
        dcsf_omega, disf_omega = self._get_data_from_files("axes/omega")

        if not np.all(dcsf_omega == disf_omega):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent omegas between dcsf and disf input files"
            )

        self._outputData.add(
            "ndsf/axes/omega", "LineOutputVariable", dcsf_omega, units="rad/ps"
        )

        # Check omega window consistency
        dcsf_omega_window, disf_omega_window = self._get_data_from_files(
            "res/omega_window"
        )

        if not np.all(dcsf_omega_window == disf_omega_window):
            raise NeutronDynamicTotalStructureFactorError(
                "Inconsistent omega windows between dcsf and disf input files"
            )

        self._outputData.add(
            "ndsf/axes/omega_window", "LineOutputVariable", dcsf_omega, units="au"
        )

        # Check f(q,t) and s(q,f) for dcsf
        for pair_str, _ in self.pair_labels:
            if (
                f"dcsf/f(q,t)/{pair_str}"
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in dcsf input file"
                )
            if (
                f"dcsf/s(q,f)/{pair_str}"
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in dcsf input file"
                )
            if (
                "scaling_factor"
                not in self.configuration["dcsf_input_file"]["instance"][
                    f"dcsf/s(q,f)/{pair_str}"
                ].attrs.keys()
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "This DCSF file was created before the new scaling scheme. Please calculate it again."
                )

        for element in self.trajectory.unique_names:
            if (
                f"disf/f(q,t)/{element}"
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in disf input file"
                )
            if (
                f"disf/s(q,f)/{element}"
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in disf input file"
                )
            if (
                "scaling_factor"
                not in self.configuration["disf_input_file"]["instance"][
                    f"disf/s(q,f)/{element}"
                ].attrs.keys()
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "This DISF file was created before the new scaling scheme. Please calculate it again."
                )

        for element in self.trajectory.unique_names:
            fqt = self.configuration["disf_input_file"]["instance"][
                f"disf/f(q,t)/{element}"
            ]
            sqf = self.configuration["disf_input_file"]["instance"][
                f"disf/s(q,f)/{element}"
            ]
            self._outputData.add(
                f"ndsf/f(q,t)_inc/{element}",
                "SurfaceOutputVariable",
                fqt,
                axis="ndsf/axes/q|ndsf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"ndsf/s(q,f)_inc/{element}",
                "SurfaceOutputVariable",
                sqf,
                axis="ndsf/axes/q|ndsf/axes/omega",
                units="nm2/ps",
            )

        for pair_str, _ in self.pair_labels:
            fqt = self.configuration["dcsf_input_file"]["instance"][
                f"dcsf/f(q,t)/{pair_str}"
            ]
            sqf = self.configuration["dcsf_input_file"]["instance"][
                f"dcsf/s(q,f)/{pair_str}"
            ]
            self._outputData.add(
                f"ndsf/f(q,t)_coh/{pair_str}",
                "SurfaceOutputVariable",
                fqt,
                axis="ndsf/axes/q|ndsf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"ndsf/s(q,f)_coh/{pair_str}",
                "SurfaceOutputVariable",
                sqf,
                axis="ndsf/axes/q|ndsf/axes/omega",
                units="nm2/ps",
            )

        nQValues = len(dcsf_q)
        nTimes = len(dcsf_time)
        nOmegas = len(dcsf_omega)

        self._outputData.add(
            "ndsf/f(q,t)_coh/total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="ndsf/axes/q|ndsf/axes/time",
            units="au",
        )
        self._outputData.add(
            "ndsf/f(q,t)_inc/total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="ndsf/axes/q|ndsf/axes/time",
            units="au",
        )
        self._outputData.add(
            "ndsf/f(q,t)/total",
            "SurfaceOutputVariable",
            (nQValues, nTimes),
            axis="ndsf/axes/q|ndsf/axes/time",
            units="au",
        )

        self._outputData.add(
            "ndsf/s(q,f)_coh/total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="ndsf/axes/q|ndsf/axes/omega",
            units="nm2/ps",
            main_result=True,
            partial_result=True,
        )
        self._outputData.add(
            "ndsf/s(q,f)_inc/total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="ndsf/axes/q|ndsf/axes/omega",
            units="nm2/ps",
            main_result=True,
            partial_result=True,
        )
        self._outputData.add(
            "ndsf/s(q,f)/total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="ndsf/axes/q|ndsf/axes/omega",
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

        nAtomsPerElement = self.trajectory.get_natoms()
        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        norm_natoms = 1.0 / n_total
        # Compute coherent functions and structure factor
        for pair_str, (label_i, label_j) in self.pair_labels:
            ele_i = self.trajectory.element_from_label[label_i]
            ele_j = self.trajectory.element_from_label[label_j]
            bi = self.trajectory.get_atom_property(ele_i, "b_coherent")
            bj = self.trajectory.get_atom_property(ele_j, "b_coherent")
            sqrt_cij = sqrt(
                nAtomsPerElement[label_i] * nAtomsPerElement[label_j] * norm_natoms**2
            )
            pre_fac = 1 if label_i == label_j else 2
            self._outputData[f"ndsf/f(q,t)_coh/{pair_str}"].scaling_factor *= (
                pre_fac * bi * bj * sqrt_cij
            ).real
            self._outputData[f"ndsf/s(q,f)_coh/{pair_str}"].scaling_factor *= (
                pre_fac * bi * bj * sqrt_cij
            ).real

            self._outputData["ndsf/f(q,t)_coh/total"][:] += (
                self._outputData[f"ndsf/f(q,t)_coh/{pair_str}"][:]
                * self._outputData[f"ndsf/f(q,t)_coh/{pair_str}"].scaling_factor
                / fact
            )
            self._outputData["ndsf/s(q,f)_coh/total"][:] += (
                self._outputData[f"ndsf/s(q,f)_coh/{pair_str}"][:]
                * self._outputData[f"ndsf/s(q,f)_coh/{pair_str}"].scaling_factor
                / fact
            )

        self._outputData["ndsf/f(q,t)_coh/total"].scaling_factor = fact
        self._outputData["ndsf/s(q,f)_coh/total"].scaling_factor = fact

        # Compute incoherent functions and structure factor
        for label, number in nAtomsPerElement.items():
            ele_i = self.trajectory.element_from_label[label]
            bi = self.trajectory.get_atom_property(ele_i, "b_incoherent")
            self._outputData[f"ndsf/f(q,t)_inc/{label}"].scaling_factor *= (
                bi**2 * number * norm_natoms
            ).real
            self._outputData[f"ndsf/s(q,f)_inc/{label}"].scaling_factor *= (
                bi**2 * number * norm_natoms
            ).real
            self._outputData["ndsf/f(q,t)_inc/total"][:] += (
                self._outputData[f"ndsf/f(q,t)_inc/{label}"][:]
                * self._outputData[f"ndsf/f(q,t)_inc/{label}"].scaling_factor
                / fact
            )
            self._outputData["ndsf/s(q,f)_inc/total"][:] += (
                self._outputData[f"ndsf/s(q,f)_inc/{label}"][:]
                * self._outputData[f"ndsf/s(q,f)_inc/{label}"].scaling_factor
                / fact
            )

        self._outputData["ndsf/f(q,t)_inc/total"].scaling_factor = fact
        self._outputData["ndsf/s(q,f)_inc/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ndsf/f(q,t)_inc",
            "SurfaceOutputVariable",
            axis="ndsf/axes/q|ndsf/axes/time",
            units="au",
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ndsf/f(q,t)_coh",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ndsf/axes/q|ndsf/axes/time",
            units="au",
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ndsf/s(q,f)_inc",
            "SurfaceOutputVariable",
            axis="ndsf/axes/q|ndsf/axes/omega",
            units="au",
            main_result=True,
            partial_result=True,
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ndsf/s(q,f)_coh",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ndsf/axes/q|ndsf/axes/omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        # Compute total F(Q,t) = inc + coh
        self._outputData["ndsf/f(q,t)/total"][:] = (
            self._outputData["ndsf/f(q,t)_coh/total"][:]
            + self._outputData["ndsf/f(q,t)_inc/total"][:]
        )
        self._outputData["ndsf/s(q,f)/total"][:] = (
            self._outputData["ndsf/s(q,f)_coh/total"][:]
            + self._outputData["ndsf/s(q,f)_inc/total"][:]
        )
        self._outputData["ndsf/f(q,t)/total"].scaling_factor = fact
        self._outputData["ndsf/s(q,f)/total"].scaling_factor = fact

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self.trajectory.close()
        self.configuration["disf_input_file"]["instance"].close()
        self.configuration["dcsf_input_file"]["instance"].close()
        super().finalize()
