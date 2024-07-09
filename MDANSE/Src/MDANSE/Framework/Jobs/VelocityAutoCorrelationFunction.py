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
from MDANSE.Mathematics.Signal import differentiate, normalize
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class VelocityAutoCorrelationFunction(IJob):
    """
    The Velocity AutoCorrelation Function (VACF) is a property describing the dynamics of a molecular system.
    It reveals the underlying nature of the forces acting on the system. Its Fourier Transform gives the cartesian density of states for a set of atoms.

    In a molecular system that would be made of non interacting particles, the velocities would be constant
    at any time giving a VACF of constant value. In the gas-phase, the magnitude and direction of the velocity of a particle
    will change gradually over time due collisions with other particles. In this case, the VACF is represented by a decaying exponential.

    In the solid phase, the interactions are much stronger and, as a result, the atoms are bound to a given, equilibrium position from
    which they move backwards and forwards.  The oscillations are not be of equal magnitude however, but decay in time, because there are
    anharmonic, perturbative forces which disrupt the oscillatory motion. In this case, the VACF looks like a damped harmonic motion.

    In the liquid phase, the atoms have more freedom than in the solid phase and because of the diffusion process, the oscillatory motion
    seen in solid phase is damped rapidly depending on the density of the system. So, the VACF tends to have one very damped oscillation
    before decaying to zero. The decaying time can be considered as the average time for a collision between two atoms.

    As well as revealing the dynamical processes in a system, the VACF has other interesting properties. Firstly, its Fourier transform,
    a.k.a as vibrational Density Of States (vDOS) can be used to reveal the underlying frequencies of the molecular processes. This is closely
    related to the infra-red spectrum of the system, which is also concerned with vibration on the molecular scale. Secondly, provided the VACF
    decays to zero at long time, the function may be integrated mathematically to calculate the diffusion coefficient D, as in:

    .. math:: D = \\frac{1}{3}\int_{0}^{+\infty}{<v(0) \cdot v(t)>dt}

    This is a special case of a more general relationship between the VACF and the mean square displacement, and belongs to a class of properties
    known as the Green-Kubo relations, which relate correlation functions to so-called transport coefficients.
    """

    label = "Velocity AutoCorrelation Function"

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
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {"label": "velocities", "dependencies": {"trajectory": "trajectory"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
    )
    settings["normalize"] = ("BooleanConfigurator", {"default": False})
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
        {"dependencies": {"atom_selection": "atom_selection"}},
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
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(log_filename)

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "vacf_%s" % element,
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="nm2/ps2",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "vacf_total",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
            units="nm2/ps2",
            main_result=True,
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

        n_configs = self.configuration["frames"]["n_configs"]
        atomicVACF = correlate(series, series[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, atomicVACF.T[0]

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
            self._outputData["vacf_%s" % element] /= number

        weights = self.configuration["weights"].get_weights()

        vacfTotal = weight(weights, self._outputData, nAtomsPerElement, 1, "vacf_%s")
        self._outputData["vacf_total"][:] = vacfTotal

        if self.configuration["normalize"]["value"]:
            for element in nAtomsPerElement.keys():
                self._outputData["vacf_%s" % element] = normalize(
                    self._outputData["vacf_%s" % element], axis=0
                )
            self._outputData["vacf_total"] = normalize(
                self._outputData["vacf_total"], axis=0
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
