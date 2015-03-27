import numpy

from Scientific.Geometry import Vector

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class ProjectorError(Error):
    pass

class Projector(object):

    __metaclass__ = REGISTRY
    
    type = 'projector'
        
    def __init__(self):
        
        self._axis = None
        
        self._projectionMatrix = None

                    
    def __call__(self, value):
        
        raise NotImplementedError
    
    def set_axis(self, axis):

        raise NotImplementedError
    
    @property
    def axis(self):
        
        return self._axis
        

class NoProjector(Projector):

    type = 'none'

    def set_axis(self, axis):
        pass
    
    def __call__(self, value):
        
        return value


class AxialProjector(Projector):

    type = 'axial'
    
    def set_axis(self, axis):
                
        try:
            self._axis = Vector(axis)
        except (TypeError,ValueError):
            raise ProjectorError('Wrong axis definition: must be a sequence of 3 floats')
        
        try:
            self._axis = self._axis.normal()
        except ZeroDivisionError:
            raise ProjectorError('The axis vector can not be the null vector')
        
        self._projectionMatrix = numpy.outer(self._axis, self._axis)

    
    def __call__(self, value):
        
        try:        
            return numpy.dot(value,self._projectionMatrix.T)
        except (TypeError,ValueError):
            raise ProjectorError("Invalid data to apply projection on")
    
class PlanarProjector(Projector):

    type = 'planar'

    def set_axis(self, axis):
                        
        try:
            self._axis = Vector(axis)
        except (TypeError,ValueError):
            raise ProjectorError('Wrong axis definition: must be a sequence of 3 floats')
        
        try:
            self._axis = self._axis.normal()
        except ZeroDivisionError:
            raise ProjectorError('The axis vector can not be the null vector')

        self._projectionMatrix = numpy.identity(3) - numpy.outer(self._axis, self._axis)

    def __call__(self, value):

        try:        
            return numpy.dot(value,self._projectionMatrix.T)
        except (TypeError,ValueError):
            raise ProjectorError("Invalid data to apply projection on")
        