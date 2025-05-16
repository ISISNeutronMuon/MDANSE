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

from MDANSE.Chemistry.GroupingTool import GroupingTool
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
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {"choices": ["atom", "average over molecules"]},
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
            "default": "b_incoherent2",
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

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)
        msd_dict = get_weights(
            {atom: 1.0 for atom in nAtomsPerElement}, nAtomsPerElement, 1
        )

        self._groupers = {}
        for key in ["fqt", "sqf", "msd"]:
            self._groupers[key] = GroupingTool(
                self.configuration["trajectory"]["instance"].chemical_system,
                self._outputData,
            )
        if self.add_ideal_results:
            self._groupers["sqf_ideal"] = GroupingTool(
                self.configuration["trajectory"]["instance"].chemical_system,
                self._outputData,
            )
        dimensions = {
            "fqt": (self._nQShells, self._nFrames),
            "sqf": (self._nQShells, self._nOmegas),
            "sqf_ideal": (self._nQShells, self._nOmegas),
            "msd": (self._nFrames,),
        }
        units = {"fqt": "au", "sqf": "nm2/ps", "sqf_ideal": "nm2/ps", "msd": "nm2"}
        axes = {
            "fqt": "q|time",
            "sqf": "q|omega",
            "sqf_ideal": "q|omega",
            "msd": "time",
        }
        name_roots = {
            "fqt": "f(q,t)",
            "sqf": "s(q,f)",
            "sqf_ideal": "s(q,f)_ideal",
            "msd": "msd",
        }
        for key, grouper in self._groupers.items():
            grouper.set_selection(
                self.configuration["atom_selection"]["flatten_indices"]
            )
            grouper.set_dataset_parameters(
                {
                    "output_type": "SurfaceOutputVariable"
                    if key != "msd"
                    else "LineOutputVariable",
                    "dimensions": dimensions[key],
                    "axis": axes[key],
                    "units": units[key],
                    "main_result": True,
                    "partial_result": True,
                }
            )
            grouper.set_weight_dictionary(weight_dict if key != "msd" else msd_dict)
            grouper.set_grouping(self.configuration["grouping_level"]["value"])
            grouper.create_result_groups(name_roots[key])
            grouper.set_atom_masses(self.configuration["trajectory"]["instance"])

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
        atomicSF, msd = x

        self._groupers["fqt"].assign_result(
            self.configuration["atom_selection"]["flatten_indices"][index],
            atomicSF,
        )
        self._groupers["msd"].assign_result(
            self.configuration["atom_selection"]["flatten_indices"][index],
            msd,
        )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        self._groupers["fqt"].finalise_centre_of_mass()

        for inkey in self._outputData.keys():
            if "f(q,t)" in inkey:
                outkey = "_".join(["s(q,f)"] + inkey.split("_")[1:])
                self._outputData[outkey][:] = get_spectrum(
                    self._outputData[inkey],
                    self.configuration["instrument_resolution"]["time_window"],
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )
                if self.add_ideal_results:
                    outkey = "_".join(["s(q,f)_ideal"] + inkey.split("_")[1:])
                    self._outputData[outkey][:] = get_spectrum(
                        self._outputData[inkey],
                        None,
                        self.configuration["instrument_resolution"]["time_step"],
                        axis=1,
                    )
        for group in self._groupers:
            if group != "fqt":
                self._groupers[group].finalise_centre_of_mass()
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
