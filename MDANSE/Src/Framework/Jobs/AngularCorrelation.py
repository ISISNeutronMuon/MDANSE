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
    settings["frames"] = ("FramesConfigurator", {"dependencies": {"trajectory": "trajectory"}})
    settings["axis_selection"] = (
        "AtomsListConfigurator",
        {
            "nAtoms": 2,
            "dependencies": {"trajectory": "trajectory"},
            "default": ("Water", ("OW", "HW")),
        },
    )
    settings["per_axis"] = (
        "BooleanConfigurator",
        {"label": "output contribution per axis", "default": False},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {"formats": ["HDFFormat", "ASCIIFormat"]})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["axis_selection"]["n_values"]

        self._outputData.add(
            "time", "LineOutputVariable", self.configuration["frames"]["duration"], units="ps"
        )

        self._outputData.add(
            "axis_index",
            "LineOutputVariable",
            np.arange(self.configuration["axis_selection"]["n_values"]),
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
                    self.configuration["axis_selection"]["n_values"],
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

        e1, e2 = self.configuration["axis_selection"]["atoms"][index]

        at1_traj = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
            e1,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        at2_traj = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
            e2,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
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

        self._outputData["ac"] /= self.configuration["axis_selection"]["n_values"]

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
