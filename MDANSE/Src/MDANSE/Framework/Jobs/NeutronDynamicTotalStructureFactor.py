# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/NeutronDynamicTotalStructureFactor.py
# @brief     Implements module/class/test NeutronDynamicTotalStructureFactor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import itertools
import os

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import correlation, get_spectrum


class NeutronDynamicTotalStructureFactorError(Error):
    pass


class NeutronDynamicTotalStructureFactor(IJob):
    """
    Computes the dynamic total structure factor for a set of atoms as the sum of the incoherent and coherent structure factors
    """

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
        {"label": "MDANSE Coherent Structure Factor", "default": "dcsf.h5"},
    )
    settings["disf_input_file"] = (
        "HDFInputFileConfigurator",
        {"label": "MDANSE Incoherent Structure Factor", "default": "disf.h5"},
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
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "ASCIIFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = 1

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
        self._elementsPairs = sorted(
            itertools.combinations_with_replacement(
                self.configuration["atom_selection"]["unique_names"], 2
            )
        )
        for pair in self._elementsPairs:
            if (
                "f(q,t)_{}{}".format(*pair)
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in dcsf input file"
                )
            if (
                "s(q,f)_{}{}".format(*pair)
                not in self.configuration["dcsf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in dcsf input file"
                )

        for element in self.configuration["atom_selection"]["unique_names"]:
            if (
                "f(q,t)_{}".format(element)
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing f(q,t) in disf input file"
                )
            if (
                "s(q,f)_{}".format(element)
                not in self.configuration["disf_input_file"]["instance"]
            ):
                raise NeutronDynamicTotalStructureFactorError(
                    "Missing s(q,f) in disf input file"
                )

        for element in self.configuration["atom_selection"]["unique_names"]:
            fqt = self.configuration["disf_input_file"]["instance"][
                "f(q,t)_{}".format(element)
            ]
            sqf = self.configuration["disf_input_file"]["instance"][
                "s(q,f)_{}".format(element)
            ]
            self._outputData.add(
                "f(q,t)_inc_%s" % element,
                "SurfaceOutputVariable",
                fqt,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_inc_%s" % element,
                "SurfaceOutputVariable",
                sqf,
                axis="q|omega",
                units="nm2/ps",
            )
            self._outputData.add(
                "f(q,t)_inc_weighted_%s" % element,
                "SurfaceOutputVariable",
                fqt.shape,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_inc_weighted_%s" % element,
                "SurfaceOutputVariable",
                sqf.shape,
                axis="q|omega",
                units="nm2/ps",
            )

        for pair in self._elementsPairs:
            fqt = self.configuration["dcsf_input_file"]["instance"][
                "f(q,t)_{}{}".format(*pair)
            ]
            sqf = self.configuration["dcsf_input_file"]["instance"][
                "s(q,f)_{}{}".format(*pair)
            ]
            self._outputData.add(
                "f(q,t)_coh_%s%s" % pair,
                "SurfaceOutputVariable",
                fqt,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_coh_%s%s" % pair,
                "SurfaceOutputVariable",
                sqf,
                axis="q|omega",
                units="nm2/ps",
            )
            self._outputData.add(
                "f(q,t)_coh_weighted_%s%s" % pair,
                "SurfaceOutputVariable",
                fqt.shape,
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_coh_weighted_%s%s" % pair,
                "SurfaceOutputVariable",
                sqf.shape,
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
        )
        self._outputData.add(
            "s(q,f)_inc_total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="q|omega",
            units="nm2/ps",
        )
        self._outputData.add(
            "s(q,f)_total",
            "SurfaceOutputVariable",
            (nQValues, nOmegas),
            axis="q|omega",
            units="nm2/ps",
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

        shell = self.configuration["q_vectors"]["shells"][index]

        if not shell in self.configuration["q_vectors"]["value"]:
            return index, None

        else:
            traj = self.configuration["trajectory"]["instance"]

            nQVectors = self.configuration["q_vectors"]["value"][shell][
                "q_vectors"
            ].shape[1]

            rho = {}
            for element in self.configuration["atom_selection"]["unique_names"]:
                rho[element] = np.zeros((self._nFrames, nQVectors), dtype=np.complex64)

            # loop over the trajectory time steps
            for i, frame in enumerate(self.configuration["frames"]["value"]):
                qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]

                conf = traj.configuration[frame]

                for element, idxs in list(self._indexesPerElement.items()):
                    selectedCoordinates = np.take(conf.array, idxs, axis=0)
                    rho[element][i, :] = np.sum(
                        np.exp(1j * np.dot(selectedCoordinates, qVectors)), axis=0
                    )

            disf_per_q_shell = {}
            for element in self.configuration["atom_selection"]["unique_names"]:
                disf_per_q_shell[element] = np.zeros((self._nFrames,), dtype=np.float64)

            for i, atom_indexes in enumerate(
                self.configuration["atom_selection"]["indexes"]
            ):
                masses = self.configuration["atom_selection"]["masses"][i]

                element = self.configuration["atom_selection"]["names"][i]

                series = read_atoms_trajectory(
                    self.configuration["trajectory"]["instance"],
                    atom_indexes,
                    first=self.configuration["frames"]["first"],
                    last=self.configuration["frames"]["last"] + 1,
                    step=self.configuration["frames"]["step"],
                    weights=[masses],
                )

                temp = np.exp(1j * np.dot(series, qVectors))
                res = correlation(temp, axis=0, average=1)

                disf_per_q_shell[element] += res

            return index, (rho, disf_per_q_shell)

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        if x is not None:
            rho, disf = x

            for pair in self._elementsPairs:
                corr = correlation(rho[pair[0]], rho[pair[1]], average=1)
                self._outputData["f(q,t)_coh_%s%s" % pair][index, :] += corr

            for k, v in list(disf.items()):
                self._outputData["f(q,t)_inc_%s" % k][index, :] += v

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()

        # Compute concentrations
        nTotalAtoms = 0
        for val in list(nAtomsPerElement.values()):
            nTotalAtoms += val

        # Compute coherent functions and structure factor
        for pair in self._elementsPairs:
            bi = ATOMS_DATABASE.get_atom_property(pair[0], "b_coherent")
            bj = ATOMS_DATABASE.get_atom_property(pair[1], "b_coherent")
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]
            ci = ni / nTotalAtoms
            cj = nj / nTotalAtoms

            self._outputData["f(q,t)_coh_weighted_%s%s" % pair][:] = (
                self._outputData["f(q,t)_coh_%s%s" % pair][:]
                * np.sqrt(ci * cj)
                * bi
                * bj
            )
            self._outputData["s(q,f)_coh_weighted_%s%s" % pair][:] = (
                self._outputData["s(q,f)_coh_%s%s" % pair][:]
                * np.sqrt(ci * cj)
                * bi
                * bj
            )
            if pair[0] == pair[1]:  # Add a factor 2 if the two elements are different
                self._outputData["f(q,t)_coh_total"][:] += self._outputData[
                    "f(q,t)_coh_weighted_%s%s" % pair
                ][:]
                self._outputData["s(q,f)_coh_total"][:] += self._outputData[
                    "s(q,f)_coh_weighted_%s%s" % pair
                ][:]
            else:
                self._outputData["f(q,t)_coh_total"][:] += (
                    2 * self._outputData["f(q,t)_coh_weighted_%s%s" % pair][:]
                )
                self._outputData["s(q,f)_coh_total"][:] += (
                    2 * self._outputData["s(q,f)_coh_weighted_%s%s" % pair][:]
                )

        # Compute incoherent functions and structure factor
        for element, ni in nAtomsPerElement.items():
            bi = ATOMS_DATABASE.get_atom_property(element, "b_incoherent2")
            ni = nAtomsPerElement[element]
            ci = ni / nTotalAtoms

            self._outputData["f(q,t)_inc_weighted_%s" % element][:] = (
                self._outputData["f(q,t)_inc_%s" % element][:] * ci * bi
            )
            self._outputData["s(q,f)_inc_weighted_%s" % element][:] = (
                self._outputData["s(q,f)_inc_%s" % element][:] * ci * bi
            )

            self._outputData["f(q,t)_inc_total"][:] += self._outputData[
                "f(q,t)_inc_weighted_%s" % element
            ][:]
            self._outputData["s(q,f)_inc_total"][:] += self._outputData[
                "s(q,f)_inc_weighted_%s" % element
            ][:]

        # Compute total F(Q,t) = inc + coh
        self._outputData["f(q,t)_total"][:] = (
            self._outputData["f(q,t)_coh_total"][:]
            + self._outputData["f(q,t)_inc_total"][:]
        )
        self._outputData["s(q,f)_total"][:] = (
            self._outputData["s(q,f)_coh_total"][:]
            + self._outputData["s(q,f)_inc_total"][:]
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )
        self.configuration["trajectory"]["instance"].close()
