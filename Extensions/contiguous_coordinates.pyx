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
                           indexes):

    cdef double x, y, z, sdx, sdy, sdz, newx, newy, newz

    cdef int i


    cdef ndarray[np.float64_t, ndim=2] contiguous_coords = np.empty((coords.shape[0],3),dtype=np.float)

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((coords.shape[0],3),dtype=np.float)

    for 0 <= i < coords.shape[0]:

        x = coords[i,0]
        y = coords[i,1]
        z = coords[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    for idxs in indexes:
        contiguous_coords[idxs[0],0] = coords[idxs[0],0]
        contiguous_coords[idxs[0],1] = coords[idxs[0],1]
        contiguous_coords[idxs[0],2] = coords[idxs[0],2]

        if len(idxs) == 1:
            continue

        for idx in idxs[1:]:

            sdx = scaleconfig[idx,0] - scaleconfig[idxs[0],0]
            sdy = scaleconfig[idx,1] - scaleconfig[idxs[0],1]
            sdz = scaleconfig[idx,2] - scaleconfig[idxs[0],2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            newx = scaleconfig[idxs[0],0] + sdx
            newy = scaleconfig[idxs[0],1] + sdy
            newz = scaleconfig[idxs[0],2] + sdz

            contiguous_coords[idx,0] = newx*cell[0,0] + newy*cell[0,1] + newz*cell[0,2]
            contiguous_coords[idx,1] = newx*cell[1,0] + newy*cell[1,1] + newz*cell[1,2]
            contiguous_coords[idx,2] = newx*cell[2,0] + newy*cell[2,1] + newz*cell[2,2]

    return contiguous_coords

def contiguous_offsets(ndarray[np.float64_t, ndim=2]  coords not None,
                           ndarray[np.float64_t, ndim=2]  cell not None,
                           ndarray[np.float64_t, ndim=2]  rcell not None,
                           indexes):

    cdef double x, y, z, sdx, sdy, sdz

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((coords.shape[0],3),dtype=np.float)

    cdef ndarray[np.float64_t, ndim=2] offsets = np.zeros((coords.shape[0],3),dtype=np.float)

    for 0 <= i < coords.shape[0]:

        x = coords[i,0]
        y = coords[i,1]
        z = coords[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    for idxs in indexes:
        if len(idxs) == 1:
            continue
        
        for idx in idxs[1:]:

            sdx = scaleconfig[idx,0] - scaleconfig[idxs[0],0]
            sdy = scaleconfig[idx,1] - scaleconfig[idxs[0],1]
            sdz = scaleconfig[idx,2] - scaleconfig[idxs[0],2]

            sdx = -round(sdx)
            sdy = -round(sdy)
            sdz = -round(sdz)

            offsets[idx,0] = sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            offsets[idx,1] = sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            offsets[idx,2] = sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]

    return offsets


            
