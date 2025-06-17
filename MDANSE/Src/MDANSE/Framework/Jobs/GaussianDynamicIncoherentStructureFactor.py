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

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement


class GaussianDynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms in the Gaussian approximation.
    """

    label = "Gaussian Dynamic Incoherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["q_shells"] = (
        "RangeConfigurator",
        {"valueType": float, "includeLast": True, "mini": 0.0},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_incoherent",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            },
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._nQShells = self.configuration["q_shells"]["number"]

        self._nFrames = self.configuration["frames"]["n_frames"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._nOmegas = self._instrResolution["n_omegas"]

        self._kSquare = self.configuration["q_shells"]["value"] ** 2

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"] != "ideal"
        )

        self.labels = [
            (element, (element,))
            for element in self.configuration["atom_selection"].get_natoms()
        ]

        self._outputData.add(
            "q",
            "LineOutputVariable",
            self.configuration["q_shells"]["value"],
            units="1/nm",
        )

        self._outputData.add("q2", "LineOutputVariable", self._kSquare, units="1/nm2")

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
            self.configuration["instrument_resolution"]["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                f"f(q,t)_{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                f"s(q,f)_{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="q|omega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                f"msd_{element}",
                "LineOutputVariable",
                (self._nFrames,),
                axis="time",
                units="nm2",
            )
            if self.add_ideal_results:
                self._outputData.add(
                    f"s(q,f)_ideal_{element}",
                    "SurfaceOutputVariable",
                    (self._nQShells, self._nOmegas),
                    axis="q|omega",
                    units="au",
                )

        self._outputData.add(
            "f(q,t)_total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nFrames),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "s(q,f)_total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nOmegas),
            axis="q|omega",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "msd_total",
            "LineOutputVariable",
            (self._nFrames,),
            axis="time",
            units="nm2",
        )
        if self.add_ideal_results:
            self._outputData.add(
                "s(q,f)_ideal_total",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="q|omega",
                units="au",
            )

        self._atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_list

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
        indices = self.configuration["atom_selection"]["indices"][index]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            indices,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        atomicSF = np.zeros((self._nQShells, self._nFrames), dtype=np.float64)

        msd = mean_square_displacement(
            series, self.configuration["frames"]["n_configs"]
        )

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
        element = self.configuration["atom_selection"]["names"][index]
        atomicSF, msd = x
        self._outputData[f"f(q,t)_{element}"] += atomicSF
        self._outputData[f"msd_{element}"] += msd

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"f(q,t)_{element}"][:] /= number
            self._outputData[f"s(q,f)_{element}"][:] = get_spectrum(
                self._outputData[f"f(q,t)_{element}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )
            self._outputData[f"msd_{element}"][:] /= number
            if self.add_ideal_results:
                self._outputData[f"s(q,f)_ideal_{element}"][:] = get_spectrum(
                    self._outputData[f"f(q,t)_{element}"],
                    None,
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )

        selected_weights, all_weights = self.configuration["weights"].get_weights()
        for weights in selected_weights, all_weights:
            for key, value in weights.items():
                weights[key] = value**2
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.configuration["atom_selection"].get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "f(q,t)_%s", self.labels)
        assign_weights(self._outputData, weight_dict, "s(q,f)_%s", self.labels)
        if self.add_ideal_results:
            assign_weights(
                self._outputData, weight_dict, "s(q,f)_ideal_%s", self.labels
            )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.configuration["atom_selection"].get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["f(q,t)_total"][:] = (
            weighted_sum(self._outputData, "f(q,t)_%s", self.labels) / fact
        )
        self._outputData["f(q,t)_total"].scaling_factor = fact
        self._outputData["s(q,f)_total"][:] = (
            weighted_sum(self._outputData, "s(q,f)_%s", self.labels) / fact
        )
        self._outputData["s(q,f)_total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "f(q,t)",
            "SurfaceOutputVariable",
            axis="q|time",
            units="au",
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "s(q,f)",
            "SurfaceOutputVariable",
            axis="q|omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.add_ideal_results:
            self._outputData["s(q,f)_ideal_total"][:] = (
                weighted_sum(self._outputData, "s(q,f)_ideal_%s", self.labels) / fact
            )
            self._outputData["s(q,f)_ideal_total"].scaling_factor = fact

            self.configuration["grouping_level"].add_grouped_totals(
                self._outputData,
                "s(q,f)_ideal",
                "SurfaceOutputVariable",
                axis="q|omega",
                units="au",
            )

        # since GDISF ~ exp(-msd * q2 / 6.0) the MSD isn't weighted in
        # the exp lets save the MSD with equal weights
        selected_weights, all_weights = self.configuration["weights"].get_weights(
            prop="equal"
        )
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.configuration["atom_selection"].get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "msd_%s", self.labels)
        self._outputData["msd_total"][:] = (
            weighted_sum(self._outputData, "msd_%s", self.labels) / fact
        )
        self._outputData["msd_total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "msd",
            "LineOutputVariable",
            axis="time",
            units="nm2",
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
