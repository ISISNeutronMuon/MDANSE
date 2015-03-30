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

@author: pellegrini
'''

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class NetCDFInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a NetCDF file.
    """
    
    type = 'netcdf_input_file'
    
    _default = ''
        
    def __init__(self, name, variables=None, **kwargs):
        
        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)
        
        self._variables = variables if variables is not None else []
           
    def configure(self, configuration, value):
                
        InputFileConfigurator.configure(self, configuration, value)
        
        if self.checkExistence:
            try:
                self['instance'] = NetCDFFile(self['value'], 'r')
                
            except IOError:
                raise ConfiguratorError("can not open %r NetCDF file for reading" % self['value'])

            for v in self._variables:
                try:                
                    self[v] = self['instance'].variables[v]
                except KeyError:
                    raise ConfiguratorError("the variable %r was not  found in %r NetCDF file" % (v,self["value"]))

    @property
    def variables(self):
        
        return self._variables

    def get_information(self):
        
        return "NetCDF input file: %r" % self["value"]