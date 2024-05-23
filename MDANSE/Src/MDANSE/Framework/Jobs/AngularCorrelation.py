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
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob


class AngularCorrelation(IJob):
    """
    Computes the angular correlation for a vector defined with respect to a molecule or set of molecules.

    Vector defined by user, starting at the origin pointing in a particular direction.
    Origin and direction can either be an atom or a centre definition (centre of a group of atoms). For example, the origin
    could be defined by the geometric centre of the head group of a surfactant molecule and the direction simply by the last atom
    of the tail or chain. The correlation is calculated for the angle formed by the same vector at
    different times

    **Calculation:** \n
    angle at time T is calculated as the following: \n
    .. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
    .. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )

    **Output:** \n
    #. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`
    #. angular_correlation_legendre_2nd: :math:`<\\frac{1}{2}(3cos(\phi(T))^{2}-1)>`

    **Usage:** \n
    This analysis is used to study molecule's orientation and rotation relaxation.
    """

    label = "Angular Correlation"

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
    settings["molecule_name"] = (
        "MoleculeSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["per_axis"] = (
        "BooleanConfigurator",
        {"label": "output contribution per axis", "default": False},
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

        ce_list = self.configuration["trajectory"][
            "instance"
        ].chemical_system.chemical_entities
        self.molecules = [
            ce
            for ce in ce_list
            if ce.name == self.configuration["molecule_name"]["value"]
        ]

        self.numberOfSteps = len(self.molecules)

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "axis_index",
            "LineOutputVariable",
            np.arange(
                self.configuration["trajectory"][
                    "instance"
                ].chemical_system.number_of_molecules(
                    self.configuration["molecule_name"]["value"]
                )
            ),
            units="au",
        )

        self._outputData.add(
            "ac",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
            units="au",
        )

        if self.configuration["per_axis"]["value"]:
            self._outputData.add(
                "ac_per_axis",
                "SurfaceOutputVariable",
                (
                    self.configuration["trajectory"][
                        "instance"
                    ].chemical_system.number_of_molecules(
                        self.configuration["molecule_name"]["value"]
                    ),
                    self.configuration["frames"]["n_frames"],
                ),
                axis="axis_index|time",
                units="au",
            )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. vectors (np.array): The calculated vectors
        """

        molecule = self.molecules[index]
        reference_atom = molecule.atom_list[0]
        chemical_system = self.configuration["trajectory"]["instance"].chemical_system

        at1_traj = np.empty((self.configuration["frames"]["number"], 3))
        at2_traj = np.empty((self.configuration["frames"]["number"], 3))

        for i, frame_index in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            )
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index
            )
            contiguous_configuration = configuration.contiguous_configuration()
            chemical_system.configuration = contiguous_configuration
            at1_traj[i] = molecule.centre_of_mass(contiguous_configuration)
            at2_traj[i] = reference_atom.centre_of_mass(contiguous_configuration)

        diff = at2_traj - at1_traj

        modulus = np.sqrt(np.sum(diff**2, 1))

        diff /= modulus[:, np.newaxis]

        n_configs = self.configuration["frames"]["number"] - self.configuration["frames"]["n_frames"] + 1
        ac = correlate(diff, diff[:n_configs], mode="valid") / (3 * n_configs)
        return index, ac.T[0]

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["ac"] += x

        if self.configuration["per_axis"]["value"]:
            self._outputData["ac_per_axis"][index, :] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._outputData["ac"] /= self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_molecules(
            self.configuration["molecule_name"]["value"]
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
