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

def cog_trajectory(ndarray[np.float64_t, ndim=3]  config not None,
                   ndarray[np.float64_t, ndim=3]  cell not None,
                   ndarray[np.float64_t, ndim=3]  rcell not None):

    cdef double x, y, z, refx, refy, refz, srefx, srefy, srefz, sx, sy, sz, sdx, sdy, sdz

    cdef int i, j

    cdef ndarray[np.float64_t, ndim=2] trajectory = np.empty((config.shape[0],3),dtype=np.float)

    # Loop over the time
    for 0 <= i < config.shape[0]:

        # The first atom is taken as reference
        refx = config[i,0,0]
        refy = config[i,0,1]
        refz = config[i,0,2]

        srefx = refx*rcell[i,0,0] + refy*rcell[i,0,1] + refz*rcell[i,0,2]
        srefy = refx*rcell[i,1,0] + refy*rcell[i,1,1] + refz*rcell[i,1,2]
        srefz = refx*rcell[i,2,0] + refy*rcell[i,2,1] + refz*rcell[i,2,2]

        # Loop over the atoms
        for 1 <= j < config.shape[1]:

            x = config[i,j,0]
            y = config[i,j,1]
            z = config[i,j,2]

            sx = x*rcell[i,0,0] + y*rcell[i,0,1] + z*rcell[i,0,2]
            sy = x*rcell[i,1,0] + y*rcell[i,1,1] + z*rcell[i,1,2]
            sz = x*rcell[i,2,0] + y*rcell[i,2,1] + z*rcell[i,2,2]

            sdx = sx - srefx
            sdy = sy - srefy
            sdz = sz - srefz

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            sx = srefx + sdx
            sy = srefy + sdy
            sz = srefz + sdz

            srefx += sx
            srefy += sy
            srefz += sz

        srefx /= config.shape[1]
        srefy /= config.shape[1]
        srefz /= config.shape[1]

        if srefx < 0.0:
            srefx += 1.0

        if srefy < 0.0:
            srefy += 1.0

        if srefz < 0.0:
            srefz += 1.0

        if srefx > 0.5:
            srefx -= 1.0

        if srefy > 0.5:
            srefy -= 1.0

        if srefz > 0.5:
            srefz -= 1.0

        trajectory[i,0] = srefx*cell[i,0,0] + srefy*cell[i,0,1] + srefz*cell[i,0,2]
        trajectory[i,1] = srefx*cell[i,1,0] + srefy*cell[i,1,1] + srefz*cell[i,1,2]
        trajectory[i,2] = srefx*cell[i,2,0] + srefy*cell[i,2,1] + srefz*cell[i,2,2]

    return trajectory

