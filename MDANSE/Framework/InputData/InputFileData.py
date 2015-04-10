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

@author: pellegrini
'''

import abc
import os

from MDANSE.Framework.InputData.IInputData import IInputData

class InputFileData(IInputData):
    
    type = None
    
    def __init__(self, filename, *args, **kwargs):
        
        super(InputFileData, self).__init__()
        
        self._filename = filename
        self._dirname = os.path.dirname(self._filename)
        self._basename = os.path.basename(self._filename)
        self._data = None
    
        self.load()

    @property
    def dirname(self):
        return self._dirname    

    @abc.abstractmethod
    def load(self):
        pass   

    @abc.abstractmethod
    def close(self):
        pass    
