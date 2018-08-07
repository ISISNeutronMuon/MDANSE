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
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

import numpy

from Scientific.Geometry import Vector

from MDANSE import REGISTRY
from MDANSE.Framework.Projectors.IProjector import IProjector, ProjectorError
    
class PlanarProjector(IProjector):

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

REGISTRY['planar'] = PlanarProjector
        