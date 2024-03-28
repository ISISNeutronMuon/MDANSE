# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/AngularCorrelation.py
# @brief     Implements module/class/test AngularCorrelation
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np


from MDANSE.Mathematics.Signal import correlation
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
        "FramesConfigurator",
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
            (self.configuration["frames"]["number"],),
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
                    self.configuration["frames"]["number"],
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

        at1_traj = np.empty((self.configuration["frames"]["n_frames"], 3))
        at2_traj = np.empty((self.configuration["frames"]["n_frames"], 3))

        for frame_index in range(
            self.configuration["frames"]["first"],
            self.configuration["frames"]["last"] + 1,
            self.configuration["frames"]["step"],
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index
            )
            contiguous_configuration = configuration.contiguous_configuration()
            chemical_system.configuration = contiguous_configuration
            at1_traj[frame_index] = molecule.centre_of_mass(contiguous_configuration)
            at2_traj[frame_index] = reference_atom.centre_of_mass(
                contiguous_configuration
            )

        diff = at2_traj - at1_traj

        modulus = np.sqrt(np.sum(diff**2, 1))

        diff /= modulus[:, np.newaxis]

        ac = correlation(diff, axis=0, average=1)

        return index, ac

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
        )

        self.configuration["trajectory"]["instance"].close()
