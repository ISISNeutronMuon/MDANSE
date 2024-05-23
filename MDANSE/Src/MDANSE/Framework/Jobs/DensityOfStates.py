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

from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import differentiate, get_spectrum
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class DensityOfStates(IJob):
    """
    The Density Of States describes the number of vibrations per unit frequency.
    In MDANSE the DOS calculation returns the Fourier transform (FT) of the weighted Velocity AutoCorrelation Function (VACF).
    With an atomic mass weighting scheme the MDANSE DOS result is proportional to the actual DOS.
    The partial DOS corresponds to selected sets of atoms or molecules.
    """

    label = "Density Of States"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {"label": "velocities", "dependencies": {"trajectory": "trajectory"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
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
            "default": "atomic_weight",
            "dependencies": {"atom_selection": "atom_selection"},
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

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        instrResolution = self.configuration["instrument_resolution"]

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="time",
            units="au",
        )

        self._outputData.add(
            "omega", "LineOutputVariable", instrResolution["omega"], units="rad/ps"
        )
        self._outputData.add(
            "romega", "LineOutputVariable", instrResolution["romega"], units="rad/ps"
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "vacf_%s" % element,
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="nm2/ps2",
            )
            self._outputData.add(
                "dos_%s" % element,
                "LineOutputVariable",
                (instrResolution["n_romegas"],),
                axis="romega",
                units="au",
            )
        self._outputData.add(
            "vacf_total",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
            units="nm2/ps2",
        )
        self._outputData.add(
            "dos_total",
            "LineOutputVariable",
            (instrResolution["n_romegas"],),
            axis="romega",
            units="au",
        )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicDOS (np.array): The calculated density of state for atom of index=index
            #. atomicVACF (np.array): The calculated velocity auto-correlation function for atom of index=index
        """

        trajectory = self.configuration["trajectory"]["instance"]

        # get atom index
        indexes = self.configuration["atom_selection"]["indexes"][index]

        if self.configuration["interpolation_order"]["value"] == 0:
            series = trajectory.read_configuration_trajectory(
                indexes[0],
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory(
                indexes[0],
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

            order = self.configuration["interpolation_order"]["value"]
            for axis in range(3):
                series[:, axis] = differentiate(
                    series[:, axis],
                    order=order,
                    dt=self.configuration["frames"]["time_step"],
                )

        series = self.configuration["projection"]["projector"](series)

        n_configs = self.configuration["frames"]["number"] - self.configuration["frames"]["n_frames"] + 1
        atomicVACF = correlate(series, series[:n_configs], mode="valid") / (3 * n_configs)
        return index, atomicVACF.T[0]

        return index, atomicVACF

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration["atom_selection"]["names"][index]

        self._outputData["vacf_%s" % element] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["vacf_%s" % element][:] /= number
            self._outputData["dos_%s" % element][:] = get_spectrum(
                self._outputData["vacf_%s" % element],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                fft="rfft",
            )

        weights = self.configuration["weights"].get_weights()
        weight(
            weights,
            self._outputData,
            nAtomsPerElement,
            1,
            "vacf_%s",
            update_values=True,
        )
        weight(
            weights, self._outputData, nAtomsPerElement, 1, "dos_%s", update_values=True
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
