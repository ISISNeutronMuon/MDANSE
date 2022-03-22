# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/distance_histogram.pyx
# @brief     Implements module/class/test distance_histogram
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
cimport numpy as np 
from numpy cimport ndarray


cdef extern from "math.h":

    double floor(double x)
    double ceil(double x)
    double sqrt(double x)

cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)

def distance_histogram(ndarray[np.float64_t, ndim=2]  config not None,
                       ndarray[np.float64_t, ndim=2]  cell not None,
                       ndarray[np.float64_t, ndim=2]  rcell not None,
                       ndarray[np.int32_t, ndim=1] indexes not None,
                       ndarray[np.int32_t, ndim=1] molindex not None,
                       ndarray[np.int32_t, ndim=1] symbolindex not None,
                       ndarray[np.float64_t, ndim=3] hintra not None,
                       ndarray[np.float64_t, ndim=3] hinter not None,
                       ndarray[np.float64_t, ndim=2] scaleconfig not None,
                       float rmin,
                       float dr):

    # This computes the intra and intermolecular distances histogram.
    # The algorithm is a Pyrex adaptation of the FORTRAN implementation 
    # made by Miguel Angel Gonzalez (Institut Laue Langevin).

    cdef double x, y, z, sdx, sdy, sdz, rx, ry, rz, r

    cdef int i, j, bin, nbins

    nbins = hinter.shape[2]

    for 0 <= i < indexes.shape[0]:

        x = config[i,0]
        y = config[i,1]
        z = config[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]
        
    for 0 <= i < indexes.shape[0] - 1:

        sx = scaleconfig[i,0]
        sy = scaleconfig[i,1]
        sz = scaleconfig[i,2]

        for i + 1 <= j < indexes.shape[0]:

            sdx = scaleconfig[j,0] - sx
            sdy = scaleconfig[j,1] - sy
            sdz = scaleconfig[j,2] - sz

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)
            
            rx = sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            ry = sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            rz = sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]

            r = sqrt(rx*rx + ry*ry + rz*rz)

            bin = <int>((r-rmin)/dr)
            
            if ( (bin < 0) or (bin >= nbins)):
                continue

            if molindex[i] == molindex[j]:
                hintra[symbolindex[i],symbolindex[j],bin] += 1.0
            else:
                hinter[symbolindex[i],symbolindex[j],bin] += 1.0
