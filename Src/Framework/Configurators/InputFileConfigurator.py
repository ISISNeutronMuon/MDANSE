import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class InputFileConfigurator(IConfigurator):
    """
    This Configurator allows to set an input file.    
    """
        
    _default = ""
    
    def __init__(self, name, wildcard="All files|*.*",**kwargs):
        '''
        Initializes the configurator object.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        '''
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._wildcard = wildcard
                
    def configure(self, value):
        '''
        Configure an input file. 
                
        :param value: the input file.
        :type value: str 
        '''
                
        value = PLATFORM.get_path(value)
                
        if not os.path.exists(value):
            raise ConfiguratorError("the input file %r does not exist." % value, self)
        
        self["value"] = value 
        self["filename"] = value
            
    @property
    def wildcard(self):
        '''
        Returns the wildcard used to filter the input file.
        
        :return: the wildcard used to filter the input file.
        :rtype: str
        '''
        
        return self._wildcard

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Input file: %r" % self["value"]
    
REGISTRY['input_file'] = InputFileConfigurator
