# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/SingleChoiceConfigurator.py
# @brief     Implements module/class/test SingleChoiceConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class SingleChoiceConfigurator(IConfigurator):
    """
     This Configurator allows to select a single item among multiple choices.
    """
        
    _default = []
            
    def __init__(self, name, choices=None, **kwargs):
        '''
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        '''
        
        IConfigurator.__init__(self, name, **kwargs)
        
        self._choices = choices if choices is not None else []

    def configure(self, value):
        '''
        Configure the input item.
                
        :param value: the input selection list.
        :type value: list
        '''

        try:
            self["index"] = self._choices.index(value)
        except ValueError:                        
            raise ConfiguratorError("%r item is not a valid choice" % value, self)
        else:        
            self["value"] = value
            
    @property
    def choices(self):
        '''
        Returns the list of allowed selection items.
        
        :return: the list of allowed selection items.
        :rtype: list
        '''
        
        return self._choices

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Selected item: %r" % self['value']
    
REGISTRY["single_choice"] = SingleChoiceConfigurator
