# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/NetCDFInputFileConfigurator.py
# @brief     Implements module/class/test NetCDFInputFileConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import nupmpy as np

import netCDF4

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class NetCDFInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a NetCDF file as input file.
    
    NetCDF is a set of software libraries and self-describing, machine-independent data formats that 
    support the creation, access, and sharing of array-oriented scientific data.
    
    For more information, please consult the NetCDF website: http://www.unidata.ucar.edu/software/netcdf/
    """
        
    _default = ''
        
    def __init__(self, name, variables=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param variables: the list of NetCDF variables that must be present in the input NetCDF file or None if there is no compulsory variable.
        :type variables: list of str or None
        '''        

        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)
        
        self._variables = variables if variables is not None else []
           
    def configure(self, value):
        '''
        Configure a NetCDF file. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the NetCDF file.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, value)
        
        try:
            self['instance'] = netCDF4.Dataset(self['value'], 'r')
            
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

    @staticmethod
    def find_numeric_variables(var_dict, group):
        """This method retrieves all the numeric variables stored in the NetCDF file.

        This is a recursive method.
        """

        for var_key in group.variables:
            if group.path == '/':
                path = '/{}'.format(var_key)
            else:
                path = '{}/{}'.format(group.path, var_key)

            comp = 1
            while var_key in var_dict:
                var_key = '{:s}_{:d}'.format(var_key, comp)
                comp += 1

            var_dict[var_key] = path

        for _, sub_group in group.groups.items():
            NetCDFInputFileConfigurator.find_numeric_variables(var_dict, sub_group)

    def get_information(self):
        '''
        Returns some basic informations about the contents of the NetCDF file.
        
        :return: the informations about the contents of the NetCDF file.
        :rtype: str
        '''
        
        info = ["NetCDF input file: %r" % self["value"]]
        
        if self.has_key('instance'):
            info.append("Contains the following variables:")
            variables = {}
            NetCDFInputFileConfigurator.find_numeric_variables(
                variables,
                '/'
            )

            for k,v in variables.items():
                info.append('{}: {}'.format(k,v))
            
        return "\n".join(info)
    
REGISTRY['netcdf_input_file'] = NetCDFInputFileConfigurator
