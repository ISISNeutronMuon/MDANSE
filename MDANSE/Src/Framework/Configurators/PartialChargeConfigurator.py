# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/PartialChargeConfigurator.py
# @brief     Implements module/class/test PartialChargeConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator,ConfiguratorError
from MDANSE.Framework.UserDefinitionStore import UD_STORE

class PartialChargeConfigurator(IConfigurator):
    """
    This configurator allows to input partial charges.
    """
        
    _default = ''
                   
    def configure(self, value):
        '''
        Configure a python script. 
                
        :param value: the path for the python script.
        :type value: str 
        '''

        trajConfig = self._configurable[self._dependencies['trajectory']]
        
        if UD_STORE.has_definition(trajConfig["basename"],'partial_charges',value):
            self.update(UD_STORE.get_definition(trajConfig["basename"],'partial_charges',value))
        else:
            if isinstance(value,str):                
                # Case of a python script
                if os.path.exists(value):
                    namespace = {}
                    
                    exec(compile(open(value, "rb").read(), value, 'exec'),self.__dict__,namespace)
                            
                    if 'charges' not in namespace:
                        raise ConfiguratorError("The variable 'charges' is not defined in the %r python script file" % (self["value"],))
                        
                    self.update(namespace)
                else:
                    raise ConfiguratorError("The python script defining partial charges %s could not be found." % value)
                    
            elif isinstance(value,dict):
                self['charges'] = value
            else:
                raise ConfiguratorError("Invalid type for partial charges.")
                
            
    def get_information(self):
        '''
        Returns some basic informations about the partial charges.
        
        :return: the informations about the partial charges.
        :rtype: str
        '''
        
        info = 'Sum of partial charges = %8.3f' % sum(self['charges'].values())
        
        return info

REGISTRY['partial_charges'] = PartialChargeConfigurator
