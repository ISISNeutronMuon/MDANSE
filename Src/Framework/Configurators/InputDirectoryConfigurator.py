import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
    
class InputDirectoryConfigurator(IConfigurator):
    '''
    This Configurator allows to set an input directory.
     
    :attention: The directory will be created at configuration time if it does not exist.
    '''
        
    _default = os.getcwd()

    def configure(self, value):
        '''
        Configure an input directory. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input directory.
        :type value: str 
        '''
        
        value = PLATFORM.get_path(value)
        
        PLATFORM.create_directory(value)
                                                
        self['value'] = value        

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Input directory: %r" % self['value']
    
REGISTRY["input_directory"] = InputDirectoryConfigurator
