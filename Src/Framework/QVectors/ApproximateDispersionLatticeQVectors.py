import collections
import itertools
import operator

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class ApproximatedDispersionQVectors(LatticeQVectors):
    """
    """
    
    settings = collections.OrderedDict()
    settings['q_start'] = ('vector', {"label":"Q start (nm^-1)","valueType":float, "notNull":False, "default":[0,0,0]})
    settings['q_end'] = ('vector', {"label":"Q end (nm^-1)", "valueType":float, "notNull":False, "default":[0,0,0]})
    settings['q_step'] = ('float', {"label":"Q step (nm^-1)", "mini":1.0e-6, "default":0.1})

    def _generate(self):

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

        if self._status is not None:
            self._status.start(len(qGroups))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for k,v in qGroups.iteritems():

            self._configuration["q_vectors"][k] = {}
            self._configuration["q_vectors"][k]['q']           = k
            self._configuration["q_vectors"][k]['q_vectors']   = vects[:,v]
            self._configuration["q_vectors"][k]['n_q_vectors'] = len(v)
            self._configuration["q_vectors"][k]['hkls']        = hkls[:,v]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
                    
REGISTRY['approximated_dispersion'] = ApproximatedDispersionQVectors
