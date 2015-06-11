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

import numpy

from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class MillerIndicesLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'miller_indices_lattice'
    
    settings = collections.OrderedDict()
    settings['shells'] = ('range', {"valueType":float, "includeLast":True, "mini":0.0})
    settings['width'] = ('float', {"mini":1.0e-6, "default":1.0})
    settings['h'] = ('range', {"includeLast":True})
    settings['k'] = ('range', {"includeLast":True})
    settings['l'] = ('range', {"includeLast":True})

    def _generate(self):
                
        hSlice = slice(self._configuration["h"]["first"],self._configuration["h"]["last"]+1,self._configuration["h"]["step"])
        kSlice = slice(self._configuration["k"]["first"],self._configuration["k"]["last"]+1,self._configuration["k"]["step"])
        lSlice = slice(self._configuration["l"]["first"],self._configuration["l"]["last"]+1,self._configuration["l"]["step"])

        # The hkl matrix (3,n_hkls)                
        hkls = numpy.mgrid[hSlice,kSlice,lSlice]
        hkls = hkls.reshape(3,hkls.size/3)
                
        # The k matrix (3,n_hkls)
        vects = numpy.dot(self._reciprocalMatrix,hkls)
        
        dists2 = numpy.sum(vects**2,axis=0)
                
        halfWidth = self._configuration["width"]["value"]/2

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        self._configuration["q_vectors"] = {}
        
        for q in self._configuration["shells"]["value"]:

            qmin = max(0,q - halfWidth)
                                    
            q2low = qmin*qmin
            q2up = (q + halfWidth)*(q + halfWidth)
            
            hits = numpy.where((dists2 >= q2low) & (dists2 <= q2up))[0]            

            nHits = len(hits)

            if nHits != 0:         
                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]['q_vectors'] = vects[:,hits]
                self._configuration["q_vectors"][q]['n_q_vectors'] = nHits
                self._configuration["q_vectors"][q]['q'] = q
                self._configuration["q_vectors"][q]['hkls'] = numpy.rint(numpy.dot(self._invReciprocalMatrix,self._configuration["q_vectors"][q]['q_vectors']))

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
