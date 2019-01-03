import numpy

from Scientific.Geometry import Vector

from MDANSE import REGISTRY
from MDANSE.Framework.Projectors.IProjector import IProjector, ProjectorError

class AxialProjector(IProjector):
    
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
        
REGISTRY['axial'] = AxialProjector
