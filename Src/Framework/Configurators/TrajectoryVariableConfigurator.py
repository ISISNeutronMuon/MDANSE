from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
          
class TrajectoryVariableConfigurator(IConfigurator):
    """
    This configurator allows to check that a given variable is actually present in a MMTK trajectory file.

    :note: this configurator depends on 'trajectory' configurator to be configured
    """
            
    _default = "velocities"
        
    def configure(self, value):
        '''
        Configure the MMTK trajectory variable.
                
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the name of the trajectory variable as it should appear in the MMTK trajectory file.
        :type value: str
        '''
                
        trajConfig = self._configurable[self._dependencies['trajectory']]
       
        if not value in trajConfig['instance'].variables():
            raise ConfiguratorError("%r is not registered as a trajectory variable." % value, self)
        
        self['value'] = value

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Selected variable: %r" % self["value"]
    
REGISTRY['trajectory_variable'] = TrajectoryVariableConfigurator
