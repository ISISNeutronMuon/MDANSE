import numpy

from Scientific.Geometry import Vector

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class VectorConfigurator(IConfigurator):
    """
    This configurator allows to input a 3D vector, by giving its 3 components
    """
        
    _default = [1.0,0.0,0.0]
    
    def __init__(self, name, valueType=int, normalize=False, notNull=False, dimension=3, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param valueType: the numeric type for the vector.
        :type valueType: int or float
        :param normalize: if True the vector will be normalized.
        :type normalize: bool
        :param notNull: if True, the vector must be non-null.
        :type notNull: bool
        :param dimension: the dimension of the vector.
        :type dimension: int
        '''

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._valueType = valueType
        
        self._normalize = normalize
        
        self._notNull = notNull
        
        self._dimension = dimension

    def configure(self, value):
        '''
        Configure a vector.
        
        :param value: the vector components.
        :type value: sequence-like object
        '''
                
        if not isinstance(value,(list,tuple)):
            raise ConfiguratorError("Invalid input type",self)
        
        if len(value) != self._dimension:
            raise ConfiguratorError("Invalid dimension",self)

        vector = Vector(numpy.array(value,dtype=self._valueType))

        if self._normalize:
            vector = vector.normal()
            
        if self._notNull:
            if vector.length() == 0.0:
                raise ConfiguratorError("The vector is null", self)

        self['vector'] = vector
        self['value'] = vector
        
    @property
    def valueType(self):
        '''
        Returns the values type of the range.
        
        :return: the values type of the range.
        :rtype: one of int or float
        '''
        
        return self._valueType

    @property
    def normalize(self):
        '''
        Returns whether or not the configured vector will be normalized.
        
        :return: True if the vector has to be normalized, False otherwise.
        :rtype: bool
        '''
        
        return self._normalize

    @property
    def notNull(self):
        '''
        Returns whether or not a null vector is accepted.
        
        :return: True if a null vector is not accepted, False otherwise.
        :rtype: bool
        '''
        
        return self._notNull
    
    @property
    def dimension(self):
        '''
        Returns the dimension of the vector.
        
        :return: the dimension of the vector.
        :rtype: int
        '''
                
        return self._dimension

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Value: %r" % self["value"]
    
REGISTRY["vector"] = VectorConfigurator
