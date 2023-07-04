# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/distance_histogram.pyx
# @brief     Implements module/class/test distance_histogram
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
import numpy as np
cimport numpy as np 
from numpy cimport ndarray


cdef extern from "math.h":

    double floor(double x)
    double ceil(double x)
    double sqrt(double x)

cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)

def box_coordinates(ndarray[np.float64_t, ndim=2] real_coords not None,
                    ndarray[np.float64_t, ndim=2] rcell not None):

    cdef double x, y, z

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] box_coords = np.empty((real_coords.shape[0],3),dtype=np.float64)

    for 0 <= i < real_coords.shape[0]:

        x = real_coords[i,0]
        y = real_coords[i,1]
        z = real_coords[i,2]

        box_coords[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        box_coords[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        box_coords[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    return box_coords

def real_coordinates(ndarray[np.float64_t, ndim=2] box_coords not None,
                     ndarray[np.float64_t, ndim=2] cell not None):

    cdef double x, y, z

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] real_coords = np.empty((box_coords.shape[0],3),dtype=np.float64)

    for 0 <= i < box_coords.shape[0]:

        x = box_coords[i,0]
        y = box_coords[i,1]
        z = box_coords[i,2]

        real_coords[i,0] = x*cell[0,0] + y*cell[0,1] + z*cell[0,2]
        real_coords[i,1] = x*cell[1,0] + y*cell[1,1] + z*cell[1,2]
        real_coords[i,2] = x*cell[2,0] + y*cell[2,1] + z*cell[2,2]

    return real_coords

            
