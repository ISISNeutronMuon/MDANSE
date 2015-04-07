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
import itertools
import operator

import numpy

from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class ApproximatedDispersionQVectors(LatticeQVectors):
    """
    """

    type = 'approximated_dispersion'
    
    configurators = collections.OrderedDict()
    configurators['q_start'] = ('vector', {"label":"Q start (nm^-1)","valueType":float, "notNull":False, "default":[0,0,0]})
    configurators['q_end'] = ('vector', {"label":"Q end (nm^-1)", "valueType":float, "notNull":False, "default":[0,0,0]})
    configurators['q_step'] = ('float', {"label":"Q step (nm^-1)", "mini":1.0e-6, "default":0.1})

    def generate(self, status=None):

        qStart = self._configuration["q_start"]["value"]
        qEnd = self._configuration["q_end"]["value"]
        qStep = self._configuration["q_step"]["value"]

        d = (qEnd-qStart).length()
        
        n = (qEnd-qStart).normal()
        nSteps = int(d/qStep)+1
        
        vects = numpy.array(qStart)[:,numpy.newaxis] + numpy.outer(n,numpy.arange(0,nSteps))*qStep
        
        hkls = numpy.rint(numpy.dot(self._invReciprocalMatrix,vects)) 
        
        dists = numpy.sqrt(numpy.sum(vects**2,axis=0))        
        dists = zip(xrange(len(dists)),dists)
        dists.sort(key=operator.itemgetter(1))
        qGroups = itertools.groupby(dists, key=operator.itemgetter(1))
        qGroups = collections.OrderedDict([(k,[item[0] for item in v]) for k,v in qGroups])

        if status is not None:
            status.start(len(qGroups))

        for k,v in qGroups.iteritems():

            self._definition["q_vectors"][k] = {}
            self._definition["q_vectors"][k]['q']           = k
            self._definition["q_vectors"][k]['q_vectors']   = vects[:,v]
            self._definition["q_vectors"][k]['n_q_vectors'] = len(v)
            self._definition["q_vectors"][k]['hkls']        = hkls[:,v]

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
            
        return self._definition["q_vectors"]