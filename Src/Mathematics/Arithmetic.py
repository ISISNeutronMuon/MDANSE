import cmath
import itertools

import numpy

def factorial(n):
    """Returns n!
    
    @param n: n.
    @type: integer
    
    @return: n!.
    @rtype: integer
    """
    
    # 0! = 1! = 1
    if n < 2:
        return 1
    else:
        # multiply is a ufunc of Numeric module
        return numpy.multiply.reduce(numpy.arange(2,n+1, dtype=numpy.float64))

def pgcd(n):
    """Computes the pgcd for a set of integers.
    
    @param n: n.
    @type: list of integers
    
    @return: pgcd([i1,i2,i3...]).
    @rtype: integer
    """   
    
    def _pgcd(a,b):
        while b: a, b = b, a%b
        return a
    
    p = _pgcd(n[0],n[1])
    
    for x in n[2:]:
        p = _pgcd(p, x)
        
    return p

def get_weights(props, contents, dim):
                                        
    normFactor = None

    weights = {}
                
    cartesianProduct = set(itertools.product(props.keys(), repeat=dim))
    for elements in cartesianProduct:
    
        n = numpy.product([contents[el] for el in elements])        
        p = numpy.product(numpy.array([props[el] for el in elements]),axis=0)
                
        fact = n*p

        weights[elements] = numpy.float64(numpy.copy(fact))
                
        if normFactor is None:
            normFactor = numpy.abs(fact)
        else:
            normFactor += numpy.abs(fact)
        
    for k in weights.keys():
        weights[k] /= numpy.float64(normFactor)
       
    return weights, normFactor

def weight(props,values,contents,dim,key,symmetric=True):
    weights = get_weights(props,contents,dim)[0]
    weightedSum = None      
    matches = dict([(key%k,k) for k in weights.keys()])
            
    for k,val in values.iteritems():
        
        if not matches.has_key(k):
            continue
                    
        if symmetric:
            permutations = set(itertools.permutations(matches[k], r=dim))
            w = sum([weights.pop(p) for p in permutations])
        else:
            w = weights.pop(matches[k])
                                
        if weightedSum is None:
            weightedSum = w*val
        else:
            weightedSum += w*val                
                                
    return weightedSum

class ComplexNumber(complex):
    
    def argument(self):
        return cmath.phase(self)
        
    def modulus(self):
        return numpy.sqrt(self*self.conjugate()).real
                