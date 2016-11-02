#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

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
