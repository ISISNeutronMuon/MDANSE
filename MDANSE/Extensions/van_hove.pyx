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


def van_hove(
    double[:,:] config_t0,
    double[:,:] config_t1,
    double[:,:] cell,
    int[:] indexes,
    int[:] molindex,
    int[:] symbolindex,
    double[:,:,:] intra,
    double[:,:,:] inter,
    double[:,:] scaleconfig_t0,
    double[:,:] scaleconfig_t1,
    double rmin,
    double dr
):
    cdef double x, y, z, sdx, sdy, sdz, rx, ry, rz, r
    cdef int i, j, bin, nbins
    nbins = intra.shape[2]

    for i in range(config_t0.shape[0] - 1):

        sx = scaleconfig_t0[i,0]
        sy = scaleconfig_t0[i,1]
        sz = scaleconfig_t0[i,2]

        for j in range(i + 1, config_t0.shape[0]):

            sdx = scaleconfig_t1[j,0] - sx
            sdy = scaleconfig_t1[j,1] - sy
            sdz = scaleconfig_t1[j,2] - sz

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
                intra[symbolindex[i],symbolindex[j],bin] += 1.0
            else:
                inter[symbolindex[i],symbolindex[j],bin] += 1.0
