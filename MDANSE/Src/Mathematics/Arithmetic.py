# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Mathematics/Arithmetic.py
# @brief     Implements module/class/test Arithmetic
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import math
import cmath
import itertools
from functools import reduce

import numpy as np

def pgcd(numbers: 'list[int]'):
    """Computes the Greatest Common Denominator
    of an iterable (e.g. list) of integer numbers.
    
    @param n: n.
    @type: list of integers
    
    @return: pgcd([i1,i2,i3...]).
    @rtype: integer
    """   

    return math.gcd(*numbers)  # this is valid since Python 3.9

def get_weights(props, contents, dim):
                                        
    normFactor = None

    weights = {}
                
    cartesianProduct = set(itertools.product(list(props.keys()), repeat=dim))
    for elements in cartesianProduct:
    
        n = np.prod([contents[el] for el in elements])        
        p = np.prod(np.array([props[el] for el in elements]),axis=0)
                
        fact = n*p

        weights[elements] = np.float64(np.copy(fact))
                
        if normFactor is None:
            normFactor = fact
        else:
            normFactor += fact
        
    for k in list(weights.keys()):
        weights[k] /= np.float64(normFactor)
       
    return weights, normFactor

def weight(props,values,contents,dim,key,symmetric=True):
    weights = get_weights(props,contents,dim)[0]
    weightedSum = None      
    matches = dict([(key%k,k) for k in list(weights.keys())])
            
    for k,val in values.items():
        
        if k not in matches:
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
        return np.abs(self)
                