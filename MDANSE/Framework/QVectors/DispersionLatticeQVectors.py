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

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class DispersionLatticeQVectors(LatticeQVectors):
    """
    """

    settings = collections.OrderedDict()
    settings['start'] = ('vector', {"valueType":int, "notNull":False, "default":[0,0,0]})
    settings['direction'] = ('vector', {"valueType":int, "notNull":True, "default":[1,0,0]})
    settings['n_steps'] = ('integer', {"label":"number of steps", "mini":1, "default":10})

    def _generate(self):

        start = self._configuration["start"]["value"]
        direction = self._configuration["direction"]["value"]
        n_steps = self._configuration["n_steps"]["value"]

        hkls = numpy.array(start)[:,numpy.newaxis] + numpy.outer(direction,numpy.arange(0,n_steps))
        
        # The k matrix (3,n_hkls)
        vects = numpy.dot(self._reciprocalMatrix,hkls)
                
        dists = numpy.sqrt(numpy.sum(vects**2,axis=0))

        if self._status is not None:
            self._status.start(len(dists))

        self._configuration["q_vectors"] = collections.OrderedDict()
                                
        for i,v in enumerate(dists):

            self._configuration["q_vectors"][v] = {}
            self._configuration["q_vectors"][v]['q_vectors'] = vects[:,i][:,numpy.newaxis]
            self._configuration["q_vectors"][v]['n_q_vectors'] = 1
            self._configuration["q_vectors"][v]['q'] = v
            self._configuration["q_vectors"][v]['hkls'] = hkls[:,i][:,numpy.newaxis]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()

REGISTRY["dispersion_lattice"] = DispersionLatticeQVectors
