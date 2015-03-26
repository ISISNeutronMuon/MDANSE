import abc
import collections
import itertools
import operator
import random

import numpy

from Scientific.Geometry import Vector

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurables.Configurators import ConfiguratorsDict
from MDANSE.Framework.Configurables.Configurable import Configurable
from MDANSE.Mathematics.Geometry import random_points_on_circle, random_points_on_sphere

class QVectorsError(Error):
    pass

class QVectors(Configurable):
    
    __metaclass__ = REGISTRY
    
    type = "q vectors"

    is_lattice = False
            
    def __init__(self, universe):
        
        Configurable.__init__(self)
                
        self._universe = universe
        
    @abc.abstractmethod
    def generate(self, status=None):
        pass
                                
class LatticeQVectors(QVectors):
    
    is_lattice = True

    type = None
    
    def __init__(self, universe):
        
        super(LatticeQVectors,self).__init__(universe)
        
        if not self._universe.is_periodic:
            raise QVectorsError("The universe must be periodic for building lattice-based Q vectors")

        self._reciprocalBasis = [2.0*numpy.pi*v for v in self._universe.reciprocalBasisVectors()]

        self._reciprocalMatrix = numpy.transpose(self._reciprocalBasis)

        self._invReciprocalMatrix = numpy.linalg.inv(self._reciprocalMatrix)

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

class GridLatticeQVectors(LatticeQVectors):
    """
    """
    
    type = 'grid'
    
    configurators = ConfiguratorsDict()
    configurators.add_item('hrange', 'range', valueType=int, includeLast=True)
    configurators.add_item('krange', 'range', valueType=int, includeLast=True)
    configurators.add_item('lrange', 'range', valueType=int, includeLast=True)
    configurators.add_item('qstep', 'float', mini=1.0e-6, default=0.01)
    
    __doc__ += configurators.build_doc()
    
    def generate(self, status=None):

        vectors = collections.OrderedDict()

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

        if status is not None:
            status.start(len(qGroups))

        for q,v in qGroups.iteritems():
                        
            vectors[q] = {}
            vectors[q]['q']           = q
            vectors[q]['q_vectors']   = vects[:,v]
            vectors[q]['n_q_vectors'] = len(v)
            vectors[q]['hkls']        = hkls[:,v]

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
                
        return vectors

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

class ApproximatedDispersionQVectors(LatticeQVectors):
    """
    """

    type = 'approximated_dispersion'
    
    configurators = ConfiguratorsDict()
    configurators.add_item('q_start','vector', label="Q start (nm^-1)",valueType=float, notNull=False, default=[0,0,0])
    configurators.add_item('q_end', 'vector', label="Q end (nm^-1)", valueType=float, notNull=False, default=[0,0,0])
    configurators.add_item('q_step', 'float', label="Q step (nm^-1)", mini=1.0e-6, default=0.1)

    __doc__ += configurators.build_doc()

    def generate(self, status=None):

        vectors = collections.OrderedDict()

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

            vectors[k] = {}
            vectors[k]['q']           = k
            vectors[k]['q_vectors']   = vects[:,v]
            vectors[k]['n_q_vectors'] = len(v)
            vectors[k]['hkls']        = hkls[:,v]

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
            
        return vectors              

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
     
class CircularLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'circular_lattice'

    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1,default=50)
    configurators.add_item('width', 'float', mini=1.0e-6, default=1.0)
    configurators.add_item('axis_1', 'vector', normalize=False, notNull=True, valueType=int, default=[1,0,0])
    configurators.add_item('axis_2', 'vector', normalize=False, notNull=True, valueType=int, default=[0,1,0])

    __doc__ += configurators.build_doc()

    def generate(self, status=None):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        vectors = collections.OrderedDict()
                
        hkls = numpy.transpose([self._configuration["axis_1"]["vector"],self._configuration["axis_2"]["vector"]])

        qVects = numpy.dot(self._reciprocalMatrix,hkls)
                                                                
        qMax = self._configuration["shells"]["last"] + 0.5*self._configuration["width"]["value"]
                
        uvMax = numpy.ceil([qMax/Vector(v).length() for v in qVects.T]) + 1
                
        idxs = numpy.mgrid[-uvMax[0]:uvMax[0]+1,-uvMax[1]:uvMax[1]+1]

        idxs = idxs.reshape(2,(2*uvMax[0]+1)*(2*uvMax[1]+1))
                
        vects = numpy.dot(qVects,idxs)

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

class SphericalLatticeQVectors(LatticeQVectors):
    """
    """

    type = 'spherical_lattice'

    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1, default=50)
    configurators.add_item('width', 'float', mini=1.0e-6, default=1.0)

    __doc__ += configurators.build_doc()

    def generate(self,status=None):
                     
        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])
                
        vectors = collections.OrderedDict()
                
        qMax = self._configuration["shells"]["last"] + 0.5*self._configuration["width"]["value"]
        
        hklMax = numpy.ceil([qMax/v.length()for v in self._reciprocalBasis]) + 1
                
        vects = numpy.mgrid[-hklMax[0]:hklMax[0]+1,-hklMax[1]:hklMax[1]+1,-hklMax[2]:hklMax[2]+1]
                
        vects = vects.reshape(3,(2*hklMax[0]+1)*(2*hklMax[1]+1)*(2*hklMax[2]+1))
                    
        vects = numpy.dot(self._reciprocalMatrix,vects)
                
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
                                
        return vectors

class LinearQVectors(QVectors):
    """
    """

    type = "linear"

    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1, default=50)
    configurators.add_item('width', 'float', mini=1.0e-6, default=1.0)
    configurators.add_item('axis', 'vector', normalize=True, notNull=True, default=[1,0,0])

    __doc__ += configurators.build_doc()

    def generate(self,status=None):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])
    
        axis = self._configuration["axis"]["vector"]
        
        width = self._configuration["width"]["value"]
        
        vectors = collections.OrderedDict()

        nVectors = self._configuration["n_vectors"]["value"]

        if status is not None:
            status.start(self._configuration["shells"]['number'])

        for q in self._configuration["shells"]["value"]:

            fact = q*numpy.sign(numpy.random.uniform(-0.5,0.5,nVectors)) + width*numpy.random.uniform(-0.5,0.5,nVectors)

            vectors[q] = {}
            vectors[q]['q_vectors'] = axis.array[:,numpy.newaxis]*fact
            vectors[q]['n_q_vectors'] = nVectors
            vectors[q]['q'] = q
            vectors[q]['hkls'] = None

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()
                                    
        return vectors

class CircularQVectors(QVectors):
    """
    """

    type = "circular"

    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1, default=50)
    configurators.add_item('width', 'float', mini=0.0, default=1.0)
    configurators.add_item('axis_1', 'vector', normalize=True, notNull=True, default=[1,0,0])
    configurators.add_item('axis_2', 'vector', normalize=True, notNull=True, default=[0,1,0])

    __doc__ += configurators.build_doc()

    def generate(self,status=None):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])

        try:
            axis = self._configuration["axis_1"]["vector"].cross(self._configuration["axis_2"]["vector"]).normal()
        except ZeroDivisionError as e:
            raise QVectorsError(str(e))

        vectors = collections.OrderedDict()

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        if status is not None:
            status.start(self._configuration["shells"]['number'])
        
        for q in self._configuration["shells"]["value"]:

            fact = q*numpy.sign(numpy.random.uniform(-0.5,0.5,nVectors)) + width*numpy.random.uniform(-0.5,0.5,nVectors)
            v = random_points_on_circle(axis, radius=1.0, nPoints=nVectors)

            vectors[q] = {}
            vectors[q]['q_vectors'] = fact*v
            vectors[q]['n_q_vectors'] = nVectors
            vectors[q]['q'] = q
            vectors[q]['hkls'] = None

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()

        return vectors

class SphericalQVectors(QVectors):
    """
    """

    type = "spherical"
    
    configurators = ConfiguratorsDict()
    configurators.add_item('seed', 'integer', mini=0, default=0)
    configurators.add_item('shells', 'range', valueType=float, includeLast=True, mini=0.0)
    configurators.add_item('n_vectors', 'integer', mini=1, default=50)
    configurators.add_item('width', 'float', mini=0.0, default=1.0)
    
    __doc__ += configurators.build_doc()
    
    def generate(self,status=None):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])

        vectors = collections.OrderedDict()

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        if status is not None:
            status.start(self._configuration["shells"]['number'])

        for q in self._configuration["shells"]["value"]:

            fact = q*numpy.sign(numpy.random.uniform(-0.5,0.5,nVectors)) + width*numpy.random.uniform(-0.5,0.5,nVectors)

            v = random_points_on_sphere(radius=1.0, nPoints=nVectors)
            
            vectors[q] = {}
            vectors[q]['q_vectors'] = fact*v
            vectors[q]['n_q_vectors'] = nVectors
            vectors[q]['q'] = q
            vectors[q]['hkls'] = None

            if status is not None:
                if status.is_stopped():
                    return None
                else:
                    status.update()

        if status is not None:
            status.finish()

        return vectors
        
if __name__ == '__main__':
    
    from MMTK.Universe import ParallelepipedicPeriodicUniverse
     
    u = ParallelepipedicPeriodicUniverse()
    u.setShape([[1,0,0],[1,1,0],[1,0,1]])
    
    v = REGISTRY["q vectors"]["dispersion_lattice"](u)
    v.setup({"start" : (1,2,2), "direction" : (1,1,0), "n_steps" : 10})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
 
    v = REGISTRY["q vectors"]["miller_indices_lattice"](u)
    v.setup({"shells" : (0,10,2.0), "n_vectors" : 5, "width" : 2.0, "h" : (0,5,1), "k" : (0,4,1), "l" : (0,3,1)})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
  
    v = REGISTRY["q vectors"]["linear_lattice"](u)
    v.setup({"shells" : (0,10,2.0), "n_vectors" : 5, "width" : 2.0})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
  
    v = REGISTRY["q vectors"]["grid"](u)
    v.setup({"hrange" : (0,10,1), "krange" : (0,10,1), "":(0,10,1), "qstep" : 0.1})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
  
    v = REGISTRY["q vectors"]["circular_lattice"](u)
    v.setup({"shells" : (0,10,2.0), "n_vectors" : 5, "width" : 2.0})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
 
    v = REGISTRY["q vectors"]["spherical_lattice"](u)
    v.setup({"shells" : (0,100,1), "n_vectors" : 50, "width" : 1})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
  
    v = REGISTRY["q vectors"]["linear"](u)
    v.setup({"shells" : (0,1,1), "n_vectors" : 10, "width" : 0.01, "axis" : [1,1,2]})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
  
    v = REGISTRY["q vectors"]["circular"](u)
    v.setup({"shells" : (-10,10,2), "n_vectors" : 5, "width" : 2.0})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
    
    v = REGISTRY["q vectors"]["spherical"](u)
    v.setup({"shells" : (0,10,2), "n_vectors" : 500, "width" : 2.0})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
          
    v = REGISTRY["q vectors"]["approximated_dispersion"](u)
    v.setup({"q_start" : (0.0,0.0,0.0), "q_end":(20.3,32.4,2.2), "q_step" : 1.0})
    for k, vects in v.generate().items():
        print "shell: %s" % k
        print vects
             
