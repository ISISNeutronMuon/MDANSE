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
from __future__ import annotations

import collections

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.LinearAlgebra import Vector
from MDANSE.Mathematics.Signal import correlation
from MDANSE.Mathematics.Transformation import Rotation


class OrderParameter(IJob):
    r"""
    The combination of NMR and MD simulation data is very powerful in the study of conformational dynamics of proteins. NMR relaxation
    spectroscopy is a unique approach for a site-specific investigation of both global tumbling and internal motions of proteins.
    The molecular motions modulate the magnetic interactions  between the nuclear spins and lead for each nuclear spin to a relaxation
    behaviour which reflects its environment.

        The relationship between microscopic motions and measured spin relaxation rates is given by Redfield's theory. The relaxation
        measurements probe the relaxation dynamics of a selected nuclear spin at only a few frequencies. Moreover, only a limited number
        of independent observables are accessible. Hence, to relate relaxation data to protein dynamics,  a dynamical model for molecular
        motions or a functional form, depending on a limited number of adjustable parameters, are required.

    The generalized order parameter, indicates the degree of spatial restriction of the internal motions of a bond vector, while the
    characteristic time is an effective correlation time, setting the time scale of the internal relaxation processes. The resulting
    values range from 0 (completely disordered) to 1 (fully ordered).

    **Calculation:** \n
    angle at time T is calculated as the following: \n
    .. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
    .. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )

    **Output:** \n
    #. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`
    #. angular_correlation_legendre_2nd: :math:`<\\frac{1}{2}(3cos(\phi(T))^{2}-1)>`

    **Acknowledgement**\n
    AOUN Bachir, PELLEGRINI Eric
    """

    enabled = False

    label = "Order parameter"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = (
        "HDFTrajectoryConfigurator",
        {},
    )
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
    settings["axis_selection"] = (
        "MultipleChoicesConfigurator",
        {
            "label": "atom indices in molecule",
            "choices": list(range(100)),
            "nChoices": 2,
            "default": [0, 1],
        },
    )
    settings["reference_direction"] = (
        "VectorConfigurator",
        {"default": [0, 0, 1], "notNull": True, "normalize": True},
    )
    settings["per_axis"] = (
        "BooleanConfigurator",
        {"label": "output contribution per axis", "default": False},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self._nFrames = self.configuration["frames"]["number"]
        self._nAxis = self.configuration["axis_selection"]["n_values"]

        self.numberOfSteps = self._nAxis

        self._outputData.add(
            "op/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        self._outputData.add(
            "op/axes/axis_index",
            "LineOutputVariable",
            np.arange(self.configuration["axis_selection"]["n_values"]),
            units="au",
        )

        self._zAxis = Vector([0, 0, 1])
        refAxis = self.configuration["reference_direction"]["value"]
        axis = self._zAxis.cross(refAxis)

        theta = np.arctan2(axis.length(), self._zAxis * refAxis)

        try:
            self._rotation = Rotation(axis, theta).tensor.array
        except ZeroDivisionError:
            self._doRotation = False
        else:
            self._doRotation = True

        self._outputData.add(
            "op/p1",
            "LineOutputVariable",
            (self._nFrames,),
            axis="op/axes/time",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "op/p2",
            "LineOutputVariable",
            (self._nFrames,),
            axis="op/axes/time",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "op/s2",
            "LineOutputVariable",
            (self._nAxis,),
            axis="op/axes/time",
            units="au",
        )

        if self.configuration["per_axis"]["value"]:
            self._outputData.add(
                "op/p1/per_axis",
                "SurfaceOutputVariable",
                (self._nAxis, self._nFrames),
                axis="op/axes/axis_index|op/axes/time",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                "op/p2/per_axis",
                "SurfaceOutputVariable",
                (self._nAxis, self._nFrames),
                axis="op/axes/axis_index|op/axes/time",
                units="au",
                main_result=True,
                partial_result=True,
            )

    def run_step(self, index):
        """
        Runs a single step of the job.

        :param index: the index of the step.
        :type index: int
        :return: a 2-tuple whose 1st element is the index of the step and 2nd element resp. p1, p2, s2 vectors.
        :rtype: 2-tuple
        """

        e1, e2 = self.configuration["axis_selection"]["atoms"][index]

        serie1 = self.trajectory.read_atomic_trajectory(
            e1,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        serie2 = self.trajectory.read_atomic_trajectory(
            e2,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        diff = serie2 - serie1

        modulus = np.sqrt(np.sum(diff**2, 1))

        diff /= modulus[:, np.newaxis]

        # shape (3,n)
        tDiff = diff.T

        if self._doRotation:
            diff = np.dot(self._rotation, tDiff)

        costheta = np.dot(self._zAxis.array, tDiff)
        sintheta = np.sqrt(np.sum(np.cross(self._zAxis, tDiff, axisb=0) ** 2, 1))

        cosphi = tDiff[0, :] / sintheta
        sinphi = tDiff[1, :] / sintheta

        tr2 = 3.0 * costheta**2 - 1.0
        cos2phi = 2.0 * cosphi**2 - 1.0
        sin2phi = 2.0 * sinphi * cosphi
        cossintheta = costheta * sintheta
        sintheta_sq = sintheta**2

        # 1st order legendre polynomia
        p1 = correlation(costheta)

        # Formula for the 2nd legendre polynomia applied to spherical coordinates
        p2 = (
            0.25 * correlation(tr2)
            + 3.00 * correlation(cosphi * cossintheta)
            + 3.00 * correlation(sinphi * cossintheta)
            + 0.75 * correlation(cos2phi * sintheta_sq)
            + 0.75 * correlation(sin2phi * sintheta_sq)
        )

        # s2 calculation (s2 = lim (t->+inf) p2)
        s2 = (
            0.75
            * (np.sum(cos2phi * sintheta_sq) ** 2 + np.sum(sin2phi * sintheta_sq) ** 2)
            + 3.00
            * (np.sum(cosphi * cossintheta) ** 2 + np.sum(sinphi * cossintheta) ** 2)
            + 0.25 * np.sum(tr2) ** 2
        ) / self._nFrames**2

        return index, (p1, p2, s2)

    def combine(self, index, x):
        """
        Combines/synchronizes the output of `run_step` method.

        :param index: the index of the step.
        :type index: int
        :param x: the output of `run_step` method.
        :type x: any python object
        """

        p1, p2, s2 = x

        self._outputData["op/p1"] += p1
        self._outputData["op/p2"] += p2
        self._outputData["op/s2"][index] = s2

        if self.configuration["per_axis"]["value"]:
            self._outputData["op/p1/per_axis"][index, :] = p1
            self._outputData["op/p2/per_axis"][index, :] = p2

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._outputData["op/p1"] /= self._nAxis
        self._outputData["op/p2"] /= self._nAxis

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
