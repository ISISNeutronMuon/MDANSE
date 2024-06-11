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

import numpy as np


from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum


class DynamicCoherentStructureFactorError(Error):
    pass


class DynamicCoherentStructureFactor(IJob):
    """
    Computes the dynamic coherent structure factor S_coh(Q,w) for a set of atoms.
        It can be compared to experimental data e.g. the energy-integrated, static structure factor S_coh(Q)
        or the dispersion and intensity of phonons.
    """

    label = "Dynamic Coherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_coherent",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["q_vectors"]["n_shells"]

        nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration["frames"]["number"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._nOmegas = self._instrResolution["n_omegas"]

        self._outputData.add(
            "q",
            "LineOutputVariable",
            self.configuration["q_vectors"]["shells"],
            units="1/nm",
        )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            self._instrResolution["time_window"],
            units="au",
        )

        self._outputData.add(
            "omega",
            "LineOutputVariable",
            self._instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        self._elementsPairs = sorted(
            itertools.combinations_with_replacement(
                self.configuration["atom_selection"]["unique_names"], 2
            )
        )
        self._indexesPerElement = self.configuration["atom_selection"].get_indexes()

        for pair in self._elementsPairs:
            self._outputData.add(
                "f(q,t)_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="q|omega",
                units="nm2/ps",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "f(q,t)_total",
            "SurfaceOutputVariable",
            (nQShells, self._nFrames),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "s(q,f)_total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="q|omega",
            units="nm2/ps",
            main_result=True,
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

                coords = traj.configuration(frame)["coordinates"]

                for element, idxs in self._indexesPerElement.items():
                    selectedCoordinates = np.take(coords, idxs, axis=0)
                    rho[element][i, :] = np.sum(
                        np.exp(1j * np.dot(selectedCoordinates, qVectors)), axis=0
                    )

            return index, rho

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        if x is not None:
            for pair in self._elementsPairs:
                corr = correlation(x[pair[0]], x[pair[1]], average=1)
                self._outputData["f(q,t)_%s%s" % pair][index, :] += corr

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for pair in self._elementsPairs:
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]
            self._outputData["f(q,t)_%s%s" % pair][:] /= np.sqrt(ni * nj)
            self._outputData["s(q,f)_%s%s" % pair][:] = get_spectrum(
                self._outputData["f(q,t)_%s%s" % pair],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )

        fqtTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "f(q,t)_%s%s",
        )

        self._outputData["f(q,t)_total"][:] = fqtTotal

        sqfTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "s(q,f)_%s%s",
        )
        self._outputData["s(q,f)_total"][:] = sqfTotal

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
