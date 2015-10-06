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
Created on May 21, 2015

:author: Eric C. Pellegrini
'''

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class NetCDFInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a NetCDF file as input file.
    
    NetCDF is a set of software libraries and self-describing, machine-independent data formats that 
    support the creation, access, and sharing of array-oriented scientific data.
    
    For more information, please consult the NetCDF website: http://www.unidata.ucar.edu/software/netcdf/
    """
    
    type = 'netcdf_input_file'
    
    _default = ''
        
    def __init__(self, configurable, name, variables=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param variables: the list of NetCDF variables that must be present in the input NetCDF file or None if there is no compulsory variable.
        :type variables: list of str or None
        '''        

        # The base class constructor.
        InputFileConfigurator.__init__(self, configurable, name, **kwargs)
        
        self._variables = variables if variables is not None else []
           
    def configure(self, value):
        '''
        Configure a MMTK trajectory file. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the MMTK trajectory file.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, value)
        
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
        '''
        Returns the list of NetCDF variables that must be present in the NetCDF file.
        
        :return: the list of NetCDF variables that must be present in the NetCDF file.
        :rtype: list of str
        '''
        
        return self._variables

    def get_information(self):
        '''
        Returns some basic informations about the contents of the MMTK trajectory file.
        
        :return: the informations about the contents of the MMTK trajectory file.
        :rtype: str
        '''
        
        info = ["NetCDF input file: %r" % self["value"]]
        
        if self.has_key('instance'):
            info.append("Contains the following variables:")
            for v in self['instance'].variables:
                info.append(v)
            
        return "\n".join(info)