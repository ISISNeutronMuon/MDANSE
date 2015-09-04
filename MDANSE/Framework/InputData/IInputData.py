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
Created on May 27, 2015

:author: Eric C. Pellegrini
'''

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class InputDataError(Error):
    '''
    This class handles exception related to ``IInputData`` interface.
    '''

class IInputData(object):
    '''
    This is the base class for handling MDANSE input data.    
    '''
    
    __metaclass__ = REGISTRY
    
    type = "input_data"

    def __init__(self,name, *args):
        '''
        Builds an ``IInputData`` object.
        '''

        self._name = name
        
        self._data = None

    @property
    def name(self):
        '''
        Returns the name associated with the input data.
        
        :return: the name associated with the input data.
        :rtype: str
        '''
        
        return self._name
    
    @property
    def shortname(self):
        
        return self._name
            
    @property
    def data(self):
        '''
        Return the input data.
        
        :return: the input data.
        :rtype: depends on the concrete ``IInputData`` subclass
        '''
        
        return self._data

    def info(self):
        '''
        Returns information as a string about the input data.
        
        :return:
        :rtype: str
        '''

        return "No information available"
