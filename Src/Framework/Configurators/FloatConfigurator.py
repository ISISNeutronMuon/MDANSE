from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class FloatConfigurator(IConfigurator):
    '''
    This Configurator allows to input a float.
    '''
        
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: float or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: float or None
        :param choices: the list of floats allowed for the input value. If None, any value will be allowed.
        :type choices: list of float or None
        '''

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._mini = float(mini) if mini is not None else None

        self._maxi = float(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []

    def configure(self, value):
        '''
        Configure an input value.
                
        :param value: the input value
        :type value: float
        '''
                        
        try:
            value = float(value)
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e,self)
            
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
        Returns the minimum value allowed for an input float.
        
        :return: the minimum value allowed for an input float.
        :rtype: float or None
        '''
        
        return self._mini

    @property
    def maxi(self):
        '''
        Returns the maximum value allowed for an input float.
        
        :return: the maximum value allowed for an input float.
        :rtype: float or None
        '''
        
        return self._maxi

    @property
    def choices(self):
        '''
        Returns the list of floats allowed for an input float.
        
        :return: the choices allowed for an input float.
        :rtype: list of floats or None
        '''
        
        return self._choices

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Value: %r" % self['value']
    
REGISTRY['float'] = FloatConfigurator
