import numpy

from MDANSE.Framework.QVectors.IQVectors import IQVectors, QVectorsError                                

class LatticeQVectors(IQVectors):
    
    is_lattice = True
    
    def __init__(self, universe,status=None):
        
        super(LatticeQVectors,self).__init__(universe,status)
                
        if not self._universe.is_periodic:
            raise QVectorsError("The universe must be periodic for building lattice-based Q vectors")

        self._reciprocalBasis = [2.0*numpy.pi*v for v in self._universe.reciprocalBasisVectors()]

        self._reciprocalMatrix = numpy.transpose(self._reciprocalBasis)

        self._invReciprocalMatrix = numpy.linalg.inv(self._reciprocalMatrix)
