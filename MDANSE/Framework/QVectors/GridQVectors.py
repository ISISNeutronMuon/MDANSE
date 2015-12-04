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
import itertools
import operator

import numpy

from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class GridLatticeQVectors(LatticeQVectors):
    """
    """
    
    type = 'grid'
    
    settings = collections.OrderedDict()
    settings['hrange'] = ('range', {"valueType":int, "includeLast":True})
    settings['krange'] = ('range', {"valueType":int, "includeLast":True})
    settings['lrange'] = ('range', {"valueType":int, "includeLast":True})
    settings['qstep'] = ('float', {"mini":1.0e-6, "default":0.01})
    
    def _generate(self):

        hrange = self._configuration["hrange"]["value"]
        krange = self._configuration["krange"]["value"]
        lrange = self._configuration["krange"]["value"]
        qstep = self._configuration["qstep"]["value"]

        nh = self._configuration["hrange"]["number"]
        nk = self._configuration["krange"]["number"]
        nl = self._configuration["lrange"]["number"]
        
        hkls = numpy.mgrid[hrange[0]:hrange[-1]+1,krange[0]:krange[-1]+1,lrange[0]:lrange[-1]+1]
        hkls = hkls.reshape(3,nh*nk*nl)
                
        # The k matrix (3,n_hkls)
        vects = numpy.dot(self._reciprocalMatrix,hkls)
        
        dists = numpy.sqrt(numpy.sum(vects**2,axis=0))
        
        minDist = dists.min()
        maxDist = dists.max()
        
        bins = numpy.arange(minDist,maxDist+qstep/2,qstep)
        inds = numpy.digitize(dists, bins)-1
            
        dists = bins[inds]
        
        dists = zip(xrange(len(dists)),dists)
        dists.sort(key=operator.itemgetter(1))
        qGroups = itertools.groupby(dists, key=operator.itemgetter(1))
        qGroups = collections.OrderedDict([(k,[item[0] for item in v]) for k,v in qGroups])

        if self._status is not None:
            self._status.start(len(qGroups))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q,v in qGroups.iteritems():
                        
            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]['q'] = q
            self._configuration["q_vectors"][q]['q_vectors'] = vects[:,v]
            self._configuration["q_vectors"][q]['n_q_vectors'] = len(v)
            self._configuration["q_vectors"][q]['hkls'] = hkls[:,v]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
