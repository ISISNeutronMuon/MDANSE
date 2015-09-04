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
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

import abc
import os

from MDANSE.Framework.InputData.IInputData import IInputData

class InputFileData(IInputData):
    
    type = None
    
    def __init__(self, filename, load=True):
                
        IInputData.__init__(self,filename)
                
        self._basename = os.path.basename(filename)
        self._dirname = os.path.dirname(filename)
    
        if load:    
            self.load()

    @property
    def filename(self):
        '''
        Returns the filename associated with the input data.
        
        :return: the filename associated with the input data.
        :rtype: str
        '''
        
        return self._name

    @property
    def shortname(self):
        '''
        Returns the shortname of the file associated with the input data.
        
        :return: the shortname of the file associated with the input data.
        :rtype: str
        '''

        return self._basename    

    @property
    def basename(self):
        '''
        Returns the basename of the file associated with the input data.
        
        :return: the basename of the file associated with the input data.
        :rtype: str
        '''

        return self._basename    
        
    @property
    def dirname(self):
        return self._dirname    

    @abc.abstractmethod
    def load(self):
        pass   

    @abc.abstractmethod
    def close(self):
        pass    
