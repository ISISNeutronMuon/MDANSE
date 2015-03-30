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

import numpy

from MDANSE.Framework.Configurators.ConfiguratorsDict import ConfiguratorsDict
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class MillerIndicesLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'miller_indices_lattice'
    
    configurators = ConfiguratorsDict()
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('width', 'float', mini=1.0e-6, default=1.0)
    configurators.add_item('h', 'range', includeLast=True)
    configurators.add_item('k', 'range', includeLast=True)
    configurators.add_item('l', 'range', includeLast=True)

    __doc__ += configurators.build_doc()

    def generate(self, status=None):
        
        vectors = collections.OrderedDict()
        
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

        if status is not None:
            status.start(len(self._configuration["shells"]["value"]))
        
        for q in self._configuration["shells"]["value"]:

            qmin = max(0,q - halfWidth)
                                    
            q2low = qmin*qmin
            q2up = (q + halfWidth)*(q + halfWidth)
            
            hits = numpy.where((dists2 >= q2low) & (dists2 <= q2up))[0]            

            nHits = len(hits)

            if nHits != 0:         
                vectors[q] = {}
                vectors[q]['q_vectors'] = vects[:,hits]
                vectors[q]['n_q_vectors'] = nHits
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