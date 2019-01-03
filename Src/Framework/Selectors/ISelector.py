# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ISelector.py
# @brief     Implements module/class/test ISelector
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc

from MDANSE.Core.Error import Error

class SelectorError(Error):
    pass

class ISelector(object):
    
    _registry = "selector"
        
    def __init__(self,trajectory):
        
        self._universe = trajectory.universe
                
        self._choices = ["*"]

    @property
    def choices(self):
        return self._choices

    @abc.abstractmethod
    def select(self):
        pass
