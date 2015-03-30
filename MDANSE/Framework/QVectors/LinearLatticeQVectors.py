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

@author: pellegrini
'''

import collections
import random

import numpy

from Scientific.Geometry import Vector

from MDANSE.Framework.Configurators.ConfiguratorsDict import ConfiguratorsDict
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class LinearLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'linear_lattice'

    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1,default=50)
    configurators.add_item('width', 'float', mini=1.0e-6, default=1.0)
    configurators.add_item('axis', 'vector', normalize=False, notNull=True, valueType=int, default=[1,0,0])

    __doc__ += configurators.build_doc()

    def generate(self, status=None):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        vectors = collections.OrderedDict()
        
        # The Q vector corresponding to the input hkl.
        qVect = numpy.dot(self._reciprocalMatrix,self._configuration["axis"]["vector"])

        qMax = self._configuration["shells"]["last"] + 0.5*self._configuration["width"]["value"]

        uMax = numpy.ceil(qMax/Vector(qVect).length()) + 1

        idxs = numpy.mgrid[-uMax:uMax+1]
        
        vects = numpy.dot(qVect[:,numpy.newaxis],idxs[numpy.newaxis,:])
                        
        dists2 = numpy.sum(vects**2,axis=0)
        
        halfWidth = self._configuration["width"]["value"]/2

        nVectors = self._configuration["n_vectors"]["value"]

        if status is not None:
            status.start(self._configuration["shells"]['number'])
        
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

                vectors[q] = {}
                vectors[q]['q_vectors'] = vects[:,hits]
                vectors[q]['n_q_vectors'] = n
                vectors[q]['q'] = q
                vectors[q]['hkls'] = numpy.rint(numpy.dot(self._invReciprocalMatrix,vectors[q]['q_vectors']))
                
            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
                
        return vectors