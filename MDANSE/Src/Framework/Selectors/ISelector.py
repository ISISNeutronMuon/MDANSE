# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ISelector.py
# @brief     Implements module/class/test ISelector
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
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


class SelectorError(Error):
    pass


class ISelector(object):
    _registry = "selector"

    def __init__(self, chemicalSystem: ChemicalSystem):
        self._chemicalSystem = chemicalSystem

        self._choices = ["*"]

    @property
    def choices(self):
        return self._choices

    @abc.abstractmethod
    def select(self):
        pass
