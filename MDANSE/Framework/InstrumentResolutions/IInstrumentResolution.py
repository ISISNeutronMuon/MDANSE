#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import abc

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable

class InstrumentResolutionError(Error):
    pass

class IInstrumentResolution(Configurable):

    __metaclass__ = REGISTRY
    
    type = "instrument_resolution"
    
    def __init__(self):
        
        Configurable.__init__(self)
                        
        self._frequencyWindow = None

        self._timeWindow = None
        
    @abc.abstractmethod
    def set_kernel(self, frequencies, dt):
        pass    
    
    @property
    def frequencyWindow(self):
        
        if self._frequencyWindow is None:
            raise InstrumentResolutionError("Undefined frequency window")
        
        return self._frequencyWindow

    @property
    def timeWindow(self):
        
        if self._timeWindow is None:
            raise InstrumentResolutionError("Undefined time window")
        
        return self._timeWindow