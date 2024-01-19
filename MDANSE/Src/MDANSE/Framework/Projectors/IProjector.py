# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Projectors/IProjector.py
# @brief     Implements module/class/test IProjector
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Core.Error import Error

from MDANSE.Core.SubclassFactory import SubclassFactory


class ProjectorError(Error):
    pass


class IProjector(metaclass=SubclassFactory):
    def __init__(self):
        self._axis = None

        self._projectionMatrix = None

    def __call__(self, value):
        raise NotImplementedError

    def set_axis(self, axis):
        raise NotImplementedError

    @property
    def axis(self):
        return self._axis