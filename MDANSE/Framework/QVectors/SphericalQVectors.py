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

import collections

import numpy

from MDANSE.Mathematics.Geometry import random_points_on_sphere
from MDANSE.Framework.QVectors.IQVectors import IQVectors

class SphericalQVectors(IQVectors):
    """
    """

    type = "spherical"
    
    settings = collections.OrderedDict()
    settings['seed'] = ('integer', {"mini":0, "default":0})
    settings['shells'] = ('range', {"valueType":float, "includeLast":True, "mini":0.0})
    settings['n_vectors'] = ('integer', {"mini":1, "default":50})
    settings['width'] = ('float', {"mini":0.0, "default":1.0})
    
    def _generate(self):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        self._configuration["q_vectors"] = collections.OrderedDict()
        
        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        for q in self._configuration["shells"]["value"]:

            fact = q*numpy.sign(numpy.random.uniform(-0.5,0.5,nVectors)) + width*numpy.random.uniform(-0.5,0.5,nVectors)

            v = random_points_on_sphere(radius=1.0, nPoints=nVectors)
            
            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]['q_vectors'] = fact*v
            self._configuration["q_vectors"][q]['n_q_vectors'] = nVectors
            self._configuration["q_vectors"][q]['q'] = q
            self._configuration["q_vectors"][q]['hkls'] = None

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
