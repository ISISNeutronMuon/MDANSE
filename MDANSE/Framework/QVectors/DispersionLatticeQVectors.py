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

class DispersionLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'dispersion_lattice'

    configurators = ConfiguratorsDict()
    configurators.add_item('start', 'vector', valueType=int, notNull=False, default=[0,0,0])
    configurators.add_item('direction', 'vector', valueType=int, notNull=True, default=[1,0,0])
    configurators.add_item('n_steps', 'integer', label="number of steps", mini=1, default=10)

    __doc__ += configurators.build_doc()

    def generate(self, status=None):

        vectors = collections.OrderedDict()

        start = self._configuration["start"]["value"]
        direction = self._configuration["direction"]["value"]
        n_steps = self._configuration["n_steps"]["value"]

        hkls = numpy.array(start)[:,numpy.newaxis] + numpy.outer(direction,numpy.arange(0,n_steps))
        
        # The k matrix (3,n_hkls)
        vects = numpy.dot(self._reciprocalMatrix,hkls)
                
        dists = numpy.sqrt(numpy.sum(vects**2,axis=0))

        if status is not None:
            status.start(len(dists))
                                
        for i,v in enumerate(dists):

            vectors[v] = {}
            vectors[v]['q_vectors'] = vects[:,i][:,numpy.newaxis]
            vectors[v]['n_q_vectors'] = 1
            vectors[v]['q'] = v
            vectors[v]['hkls'] = hkls[:,i][:,numpy.newaxis]

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
                
        return vectors