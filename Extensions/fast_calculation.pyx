# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/fast_calculation.pyx
# @brief     Implements module/class/test fast_calculation
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
cimport numpy as np
from numpy cimport ndarray

cdef extern from "math.h":
    double sqrt(double x)

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def cpt_cluster_connectivity(ndarray[np.float64_t, ndim=2] coords, 
                                ndarray[np.float64_t, ndim=1] covRadii, 
                                np.float32_t tolerance,
                                bonds):
    '''
    Compute the connectivity of an atom cluster.
    '''
    
    cdef int i, j, nbat
    cdef float radius, distance
    nbat = len(covRadii)
    
    for i in range(nbat-1):
        radiusi = covRadii[i] + tolerance
        for j in range(i+1,nbat):
            radius = radiusi + covRadii[j]
            distance = (coords[i,0] - coords[j,0])**2 + (coords[i,1] - coords[j,1])**2 + (coords[i,2] - coords[j,2])**2
            if distance <= (radius*radius):
                bonds.append([i,j])
    return bonds

                
