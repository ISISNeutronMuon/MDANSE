
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
cimport numpy as np 
from numpy cimport ndarray


cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)
    double sqrt(double x)


cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def distance_histogram(double[:,:]  config,
                       double[:,:]  cell,
                       double[:,:]  rcell,
                       int[:] indexes,
                       int[:] molindex,
                       int[:] symbolindex,
                       double[:,:,:] hintra,
                       double[:,:,:] hinter,
                       double[:,:] scaleconfig,
                       float rmin,
                       float dr):

    # This computes the intra and intermolecular distances histogram.
    # The algorithm is a Pyrex adaptation of the FORTRAN implementation 
    # made by Miguel Angel Gonzalez (Institut Laue Langevin).

    cdef double x, y, z, sdx, sdy, sdz, rx, ry, rz, r, sx, sy, sz, count

    cdef int i, j, bin, nbins

    nbins = hinter.shape[2]

    for i in range(config.shape[0]):

        x = config[i,0]
        y = config[i,1]
        z = config[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]
        
    for i in range(indexes.shape[0]):

        sx = scaleconfig[i,0]
        sy = scaleconfig[i,1]
        sz = scaleconfig[i,2]

        for j in range(i + 1, config.shape[0]):

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

            if j > indexes.shape[0]:
                count = 0.5
            else:
                count = 1.0

            if molindex[i] == molindex[j]:
                hintra[symbolindex[i],symbolindex[j],bin] += count
            else:
                hinter[symbolindex[i],symbolindex[j],bin] += count
