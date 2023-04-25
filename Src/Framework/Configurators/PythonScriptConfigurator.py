# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/PythonScriptConfigurator.py
# @brief     Implements module/class/test PythonScriptConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class PythonScriptConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a Python script.
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
        Configure a python script. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the python script.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, value)
        
        namespace = {}
        
        execfile(value,self.__dict__,namespace)
                
        for v in self._variables:
            if not namespace.has_key(v):
                raise ConfiguratorError("The variable %r is not defined in the %r python script file" % (v,self["value"]))
            
        self.update(namespace)
        
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
    
REGISTRY['python_script'] = PythonScriptConfigurator
