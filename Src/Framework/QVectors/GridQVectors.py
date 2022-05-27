# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/GridQVectors.py
# @brief     Implements module/class/test GridQVectors
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import itertools
import operator

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class GridLatticeQVectors(LatticeQVectors):
    """
    """
        
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
        
        hkls = np.mgrid[hrange[0]:hrange[-1]+1,krange[0]:krange[-1]+1,lrange[0]:lrange[-1]+1]
        hkls = hkls.reshape(3,nh*nk*nl)
                
        # The k matrix (3,n_hkls)
        vects = np.dot(self._inverseUnitCell,hkls)
        
        dists = np.sqrt(np.sum(vects**2,axis=0))
        
        minDist = dists.min()
        maxDist = dists.max()
        
        bins = np.arange(minDist,maxDist+qstep/2,qstep)
        inds = np.digitize(dists, bins)-1
            
        dists = bins[inds]
        
        dists = zip(range(len(dists)),dists)
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

REGISTRY["grid"] = GridLatticeQVectors
