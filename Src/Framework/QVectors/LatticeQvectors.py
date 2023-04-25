# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/LatticeQvectors.py
# @brief     Implements module/class/test LatticeQvectors
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
