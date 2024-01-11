# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/IQVectors.py
# @brief     Implements module/class/test IQVectors
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc

from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable

from MDANSE.Core.SubclassFactory import SubclassFactory


class QVectorsError(Error):
    pass


class IQVectors(Configurable, metaclass=SubclassFactory):
    is_lattice = False

    def __init__(self, chemical_system, status=None):
        Configurable.__init__(self)

        self._chemical_system = chemical_system

        self._status = status

    @abc.abstractmethod
    def _generate(self):
        pass

    def generate(self):
        self._generate()

        if self._status is not None:
            self._status.finish()

    def setStatus(self, status):
        self._status = status
