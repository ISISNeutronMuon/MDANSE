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

def contiguous_coordinates(ndarray[np.float64_t, ndim=2]  coords not None,
                           ndarray[np.float64_t, ndim=2]  cell not None,
                           ndarray[np.float64_t, ndim=2]  rcell not None,
                           ndarray[np.int32_t, ndim=1] indexes not None,
                           ndarray[np.float64_t, ndim=2]  contiguous_coords not None):

    cdef double x, y, z, sdx, sdy, sdz, newx, newy, newz

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((indexes.shape[0],3),dtype=np.float)

    for 0 <= i < indexes.shape[0]:

        x = coords[indexes[i],0]
        y = coords[indexes[i],1]
        z = coords[indexes[i],2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    contiguous_coords[indexes[0],0] = coords[indexes[0],0]
    contiguous_coords[indexes[0],1] = coords[indexes[0],1]
    contiguous_coords[indexes[0],2] = coords[indexes[0],2]

    for 1 <= i < indexes.shape[0]:

        sdx = scaleconfig[i,0] - scaleconfig[0,0]
        sdy = scaleconfig[i,1] - scaleconfig[0,1]
        sdz = scaleconfig[i,2] - scaleconfig[0,2]

        sdx -= round(sdx)
        sdy -= round(sdy)
        sdz -= round(sdz)

        newx = scaleconfig[0,0] + sdx
        newy = scaleconfig[0,1] + sdy
        newz = scaleconfig[0,2] + sdz

        contiguous_coords[indexes[i],0] = newx*cell[0,0] + newy*cell[0,1] + newz*cell[0,2]
        contiguous_coords[indexes[i],1] = newx*cell[1,0] + newy*cell[1,1] + newz*cell[1,2]
        contiguous_coords[indexes[i],2] = newx*cell[2,0] + newy*cell[2,1] + newz*cell[2,2]




            
