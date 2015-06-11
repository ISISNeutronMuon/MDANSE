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

@author: Eric C. Pellegrini
'''

import collections
import random

import numpy

from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class SphericalLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'spherical_lattice'

    settings = collections.OrderedDict()
    settings['seed'] = ('integer', {"mini":0, "default":0})
    settings['shells'] = ('range', {"valueType":float, "includeLast":True, "mini":0.0})
    settings['n_vectors'] = ('integer', {"mini":1, "default":50})
    settings['width'] = ('float', {"mini":1.0e-6, "default":1.0})

    def _generate(self):
                     
        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])
                
        qMax = self._configuration["shells"]["last"] + 0.5*self._configuration["width"]["value"]
        
        hklMax = numpy.ceil([qMax/v.length()for v in self._reciprocalBasis]) + 1
                
        vects = numpy.mgrid[-hklMax[0]:hklMax[0]+1,-hklMax[1]:hklMax[1]+1,-hklMax[2]:hklMax[2]+1]
                
        vects = vects.reshape(3,(2*hklMax[0]+1)*(2*hklMax[1]+1)*(2*hklMax[2]+1))
                    
        vects = numpy.dot(self._reciprocalMatrix,vects)
                
        dists2 = numpy.sum(vects**2,axis=0)
                
        halfWidth = self._configuration["width"]["value"]/2
        
        nVectors = self._configuration["n_vectors"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]['number'])

        self._configuration["q_vectors"] = {}

        for q in self._configuration["shells"]["value"]:
                                    
            qmin = max(0,q - halfWidth)
                                    
            q2low = qmin*qmin
            q2up = (q + halfWidth)*(q + halfWidth)
            
            hits = numpy.where((dists2 >= q2low) & (dists2 <= q2up))[0]            

            nHits = len(hits)
                                    
            if nHits != 0:

                n = min(nHits,nVectors)

                if nHits > nVectors:
                    hits = random.sample(hits,nVectors)

                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]['q_vectors'] = vects[:,hits]
                self._configuration["q_vectors"][q]['n_q_vectors'] = n
                self._configuration["q_vectors"][q]['q'] = q
                self._configuration["q_vectors"][q]['hkls'] = numpy.rint(numpy.dot(self._invReciprocalMatrix,
                                                                                self._configuration["q_vectors"][q]['q_vectors']))

            if self._status is not None:
                if self._status.is_stopped():
                    return None
                else:
                    self._status.update()
