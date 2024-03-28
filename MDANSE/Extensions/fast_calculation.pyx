
#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import cython
import numpy as np
cimport numpy as np 


cdef extern from "math.h":

    double floor(double x)
    double ceil(double x)
    double sqrt(double x)


cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def cpt_cluster_connectivity_nopbc(
    np.ndarray[np.float64_t, ndim=2] coords,
    np.ndarray[np.float64_t, ndim=1] covRadii,
    np.float32_t tolerance):

    '''
    Compute the connectivity of an atom cluster.
    '''
    bonds = []
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


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def cpt_cluster_connectivity_pbc(
    np.ndarray[np.float64_t, ndim=2] coords,
    np.ndarray[np.float64_t, ndim=2] cell not None,
    np.ndarray[np.float64_t, ndim=2] rcell not None,
    np.ndarray[np.float64_t, ndim=1] covRadii,
    np.float32_t tolerance,
    bonds):

    '''
    Compute the connectivity of an atom cluster.
    '''
    
    cdef int i, j, nbat

    cdef float radius, distance, sdx, sdy, sdz, rx, ry, rz, r

    nbat = len(covRadii)

    cdef np.ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((coords.shape[0],3),dtype=np.float64)

    for 0 <= i < coords.shape[0]:

        x = coords[i,0]
        y = coords[i,1]
        z = coords[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    for i in range(nbat-1):
        
        radiusi = covRadii[i] + tolerance

        for j in range(i+1,nbat):
            radius = radiusi + covRadii[j]

            sdx = scaleconfig[j,0] - scaleconfig[i,0]
            sdy = scaleconfig[j,1] - scaleconfig[i,1]
            sdz = scaleconfig[j,2] - scaleconfig[i,2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            rx = sdx*cell[0,0] + sdy*cell[0,1] + sdz*cell[0,2]
            ry = sdx*cell[1,0] + sdy*cell[1,1] + sdz*cell[1,2]
            rz = sdx*cell[2,0] + sdy*cell[2,1] + sdz*cell[2,2]

            r = rx*rx + ry*ry + rz*rz

            if r <= (radius*radius):
                bonds.append([i,j])

    return bonds

                

