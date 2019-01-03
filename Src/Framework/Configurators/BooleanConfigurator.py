# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/BooleanConfigurator.py
# @brief     Implements module/class/test BooleanConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
    
class BooleanConfigurator(IConfigurator):
    """
    This Configurator allows to input a Boolean Value (True or False).
    
    The input value can be directly provided as a Python boolean or by the using the following (standard)
     representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
    """
    
    _default = False
    
    _shortCuts = {True  : True, "true"  : True , "yes" : True, "y" : True, "1" : True, 1 : True,
                  False : False, "false" : False, "no"  : False, "n" : False, "0" : False, 0 : False}
    
    def configure(self, value):
        '''
        Configure an input value. 
        
        The value must be one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0.
        
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input value
        :type value: one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
        '''

        if not self._shortCuts.has_key(value):
            raise ConfiguratorError('the input value can not be interpreted as a boolean', self)
                        
        self["value"] = self._shortCuts[value]
                                                
    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Value: %r" % self['value']
    
REGISTRY["boolean"] = BooleanConfigurator
