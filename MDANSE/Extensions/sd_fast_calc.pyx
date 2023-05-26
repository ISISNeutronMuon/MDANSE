# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/sd_fast_calc.pyx
# @brief     Implements module/class/test sd_fast_calc
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
cimport numpy as np 
import numpy as np
from numpy cimport ndarray


cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)
    double sqrt(double x)
    double fmod(double x, double y)
    double abs(double x)
    float  fminf(float x, float y)
    
cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)


cdef inline double mod(double x, double y):
    return abs(fmod(x,y))
     
def pmod(x,y):
    return mod(x,y)
 
def spatial_density(ndarray[np.float64_t, ndim=2]  config not None,
                      ndarray[np.int32_t, ndim=1] indexes not None,
                      ndarray[np.float64_t, ndim=2]  cell not None,
                      ndarray[np.float64_t, ndim=2]  rcell not None,
                      ndarray[np.float64_t, ndim=2]  origins not None,
                      ndarray[np.float64_t, ndim=3]  bases not None,
                      ndarray[np.float64_t, ndim=1] mini not None,
                      np.float64_t resolution,
                      ndarray[np.int32_t, ndim=3] hist not None):
    

    cdef double x, y, z, sdx, sdy, sdz, minix, miniy, miniz
    cdef double xorigin, yorigin, zorigin, orthx, orthy, orthz
    cdef double aa, bb, cc, dd, ee, ff, gg, hh, ii,  denum, micx, micy, micz, xscaledOrigin, yscaledOrigin, zscaledOrigin, xscaledMin, yscaledMin, zscaledMin
    cdef int i, j,k, bin, nbins, nbases, nindexes, xind, yind, zind
    
    nbases = bases.shape[0]
    nindexes = indexes.shape[0]
        
    minix = mini[0]
    miniy = mini[1]
    miniz = mini[2]
    
    cdef ndarray[np.float64_t, ndim=2] invBasis = np.zeros((3,3), dtype = np.float64)
    cdef ndarray[np.float64_t, ndim=2] basis = np.zeros((3,3), dtype = np.float64)
    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.zeros((nindexes,3), dtype = np.float64)
        
    for 0 <= i < nindexes:

        x = <float> config[i,0]
        y = <float> config[i,1]
        z = <float> config[i,2]
        
        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]
        
    for 0 <= i < nbases:
        
        xorigin = origins[i,0]
        yorigin = origins[i,1]
        zorigin = origins[i,2]
        
        xscaledOrigin = xorigin*rcell[0,0] + yorigin*rcell[0,1] + zorigin*rcell[0,2]
        yscaledOrigin = xorigin*rcell[1,0] + yorigin*rcell[1,1] + zorigin*rcell[1,2]
        zscaledOrigin = xorigin*rcell[2,0] + yorigin*rcell[2,1] + zorigin*rcell[2,2]
        
        basis = bases[i,:,:]

        m00 = <float>basis[0,0]
        m01 = <float>basis[0,1]
        m02 = <float>basis[0,2]
        
        m10 = <float>basis[1,0]
        m11 = <float>basis[1,1]
        m12 = <float>basis[1,2]
        
        m20 = <float>basis[2,0]
        m21 = <float>basis[2,1]
        m22 = <float>basis[2,2]
        
        denum = -m02*m11*m20 + m01*m12*m20 + m02*m10*m21 - m00*m12*m21- m01*m10*m22 + m00*m11*m22
        
        invBasis[0,0] = (-m12*m21+m11*m22)/denum
        invBasis[0,1] = ( m02*m21-m01*m22)/denum
        invBasis[0,2] = (-m02*m11+m01*m12)/denum
        
        invBasis[1,0] = ( m12*m20-m10*m22)/denum
        invBasis[1,1] = (-m02*m20+m00*m22)/denum
        invBasis[1,2] = ( m02*m10-m00*m12)/denum
        
        invBasis[2,0] = (-m11*m20+m10*m21)/denum
        invBasis[2,1] = ( m02*m20-m00*m21)/denum
        invBasis[2,2] = (-m02*m10+m00*m11)/denum
                
        xscaledMin = <float> (invBasis[0,0]*minix + invBasis[0,1]*miniy + invBasis[0,2]*miniz) 
        yscaledMin = <float> (invBasis[1,0]*minix + invBasis[1,1]*miniy + invBasis[1,2]*miniz)
        zscaledMin = <float> (invBasis[2,0]*minix + invBasis[2,1]*miniy + invBasis[2,2]*miniz)
                
        for 0 <= j < nindexes:
 
            sdx = scaleconfig[j,0] - xscaledOrigin
            sdy = scaleconfig[j,1] - yscaledOrigin
            sdz = scaleconfig[j,2] - zscaledOrigin

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            micx =  sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            micy =  sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            micz =  sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]
            
            orthx = <float> (invBasis[0,0]*micx + invBasis[0,1]*micy + invBasis[0,2]*micz) 
            orthy = <float> (invBasis[1,0]*micx + invBasis[1,1]*micy + invBasis[1,2]*micz)
            orthz = <float> (invBasis[2,0]*micx + invBasis[2,1]*micy + invBasis[2,2]*micz)
            
            x = (orthx-xscaledMin)/resolution
            y = (orthy-yscaledMin)/resolution
            z = (orthz-zscaledMin)/resolution
            
            xind = <int> x
            yind = <int> y
            zind = <int> z
            
            hist[xind,yind,zind] += 1

    return hist