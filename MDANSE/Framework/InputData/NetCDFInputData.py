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

import collections

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData

class NetCDFInputData(InputFileData):
    
    type = "netcdf_data"
    
    extension = "nc"
    
    def load(self):
        
        try:
            self._netcdf = NetCDFFile(self._name,"r")
            
        except IOError:
            raise InputDataError("The data stored in %r filename could not be loaded properly." % self._name)

        else:
            self._data = collections.OrderedDict()
            variables = self._netcdf.variables
            for k in variables:
                self._data[k]={}
                try :
                    if vars[k].axis:
                        self._data[k]['axis'] =  variables[k].axis.split('|')
                    else:
                        self._data[k]['axis'] = []
                except:
                    self._data[k]['axis'] = []
                self._data[k]['data'] = variables[k].getValue()
                self._data[k]['units'] = getattr(variables[k], 'units', 'au')

    def close(self):
        self._netcdf.close()
        
    @property
    def netcdf(self):
        
        return self._netcdf
