# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Projectors/AxialProjector.py
# @brief     Implements module/class/test AxialProjector
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy as np

from MDANSE.Mathematics.LinearAlgebra import Vector

from MDANSE import REGISTRY
from MDANSE.Framework.Projectors.IProjector import IProjector, ProjectorError


class AxialProjector(IProjector):
    def set_axis(self, axis):
        try:
            self._axis = Vector(axis)
        except (TypeError, ValueError):
            raise ProjectorError(
                "Wrong axis definition: must be a sequence of 3 floats"
            )

        try:
            self._axis = self._axis.normal()
        except ZeroDivisionError:
            raise ProjectorError("The axis vector can not be the null vector")

        self._projectionMatrix = np.outer(self._axis, self._axis)

    def __call__(self, value):
        try:
            return np.dot(value, self._projectionMatrix.T)
        except (TypeError, ValueError):
            raise ProjectorError("Invalid data to apply projection on")


REGISTRY["axial"] = AxialProjector
