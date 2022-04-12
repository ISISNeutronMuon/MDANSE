# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/IntegerConfigurator.py
# @brief     Implements module/class/test IntegerConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
    
class IntegerConfigurator(IConfigurator):
    """
    This Configurator allows to input an integer.
    """
        
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: int or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: int or None
        :param choices: the list of integers allowed for the input value. If None, any value will be allowed.
        :type choices: int-list or None
        '''
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._mini = int(mini) if mini is not None else None

        self._maxi = int(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []          
                
    def configure(self, value):
        '''
        Configure an integer value.
                
        :param value: the integer to be configured.
        :type value: int
        '''

        try:
            value = int(value)
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value < self._mini:
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value > self._maxi:
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value

    @property
    def mini(self):
        '''
        Returns the minimum value allowed for an input integer.
        
        :return: the minimum value allowed for an input value integer.
        :rtype: int or None
        '''
                        
        return self._mini

    @property
    def maxi(self):
        '''
        Returns the maximum value allowed for an input integer.
        
        :return: the maximum value allowed for an input value integer.
        :rtype: int or None
        '''
                
        return self._maxi

    @property
    def choices(self):
        '''
        Returns the list of integers allowed for an input float.
        
        :return: the choices allowed for an input float.
        :rtype: int-list or None
        '''
        
        return self._choices

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Value: %r" % self["value"]
    
REGISTRY['integer'] = IntegerConfigurator
