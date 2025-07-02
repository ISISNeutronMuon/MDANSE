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
            "gdisf/axes/q",
            "LineOutputVariable",
            self.configuration["q_shells"]["value"],
            units="1/nm",
        )

        self._outputData.add(
            "gdisf/axes/q2", "LineOutputVariable", self._kSquare, units="1/nm2"
        )

        self._outputData.add(
            "gdisf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "gdisf/res/time_window",
            "LineOutputVariable",
            self._instrResolution["time_window"],
            units="au",
        )

        self._outputData.add(
            "gdisf/axes/omega",
            "LineOutputVariable",
            self.configuration["instrument_resolution"]["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "gdisf/res/omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="gdisf/axes/omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
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
        self._outputData[f"gdisf/f(q,t)/{element}"] += atomicSF
        self._outputData[f"msd/{element}"] += msd

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"gdisf/f(q,t)/{element}"][:] /= number
            self._outputData[f"gdisf/s(q,f)/{element}"][:] = get_spectrum(
                self._outputData[f"gdisf/f(q,t)/{element}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )
            self._outputData[f"msd/{element}"][:] /= number
            if self.add_ideal_results:
                self._outputData[f"gdisf/s(q,f)/ideal/{element}"][:] = get_spectrum(
                    self._outputData[f"gdisf/f(q,t)/{element}"],
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
        assign_weights(self._outputData, weight_dict, "gdisf/f(q,t)/%s", self.labels)
        assign_weights(self._outputData, weight_dict, "gdisf/s(q,f)/%s", self.labels)
        if self.add_ideal_results:
            assign_weights(
                self._outputData, weight_dict, "gdisf/s(q,f)/ideal/%s", self.labels
            )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.configuration["atom_selection"].get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["gdisf/f(q,t)/total"][:] = (
            weighted_sum(self._outputData, "gdisf/f(q,t)/%s", self.labels)
        ) / fact
        self._outputData["gdisf/s(q,f)/total"][:] = (
            weighted_sum(self._outputData, "gdisf/s(q,f)/%s", self.labels)
        ) / fact
        self._outputData["gdisf/f(q,t)/total"].scaling_factor = fact
        self._outputData["gdisf/s(q,f)/total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "gdisf/f(q,t)",
            "SurfaceOutputVariable",
            axis="gdisf/axes/q|gdisf/axes/time",
            units="au",
        )
        self.configuration["grouping_level"].add_grouped_totals(
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

            self.configuration["grouping_level"].add_grouped_totals(
                self._outputData,
                "gdisf/s(q,f)/ideal",
                "SurfaceOutputVariable",
                axis="gdisf/axes/q|gdisf/axes/omega",
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

        assign_weights(self._outputData, weight_dict, "msd/%s", self.labels)
        self._outputData["msd/total"][:] = (
            weighted_sum(self._outputData, "msd/%s", self.labels) / fact
        )

        self._outputData["msd/total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "msd",
            "LineOutputVariable",
            axis="gdisf/axes/time",
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
