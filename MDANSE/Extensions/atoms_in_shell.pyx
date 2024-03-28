
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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now

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

def atoms_in_shell_real(ndarray[np.float64_t, ndim=2]  config not None,
                        ndarray[np.float64_t, ndim=2]  cell not None,
                        ndarray[np.float64_t, ndim=2]  rcell not None,
                        int refIndex,
                        float mini,
                        float maxi):

    cdef double x, y, z, refx, refy, refz, refsx, refsy, refsz, sdx, sdy, sdz, rx, ry, rz, r2

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((config.shape[0], 3), dtype=np.float64)

    cdef double mini2 = mini**2
    cdef double maxi2 = maxi**2

    refx = config[refIndex, 0]
    refy = config[refIndex, 1]
    refz = config[refIndex, 2]

    for 0 <= i < config.shape[0]:

        x = config[i, 0]
        y = config[i, 1]
        z = config[i, 2]

        scaleconfig[i, 0] = x*rcell[0, 0] + y*rcell[0, 1] + z*rcell[0, 2]
        scaleconfig[i, 1] = x*rcell[1, 0] + y*rcell[1, 1] + z*rcell[1, 2]
        scaleconfig[i, 2] = x*rcell[2, 0] + y*rcell[2, 1] + z*rcell[2, 2]

    refsx = scaleconfig[refIndex, 0]
    refsy = scaleconfig[refIndex, 1]
    refsz = scaleconfig[refIndex, 2]

    indexes = []

    for 0 <= i < config.shape[0]:

        if i == refIndex:
            continue

        sdx = scaleconfig[i, 0] - refsx
        sdy = scaleconfig[i, 1] - refsy
        sdz = scaleconfig[i, 2] - refsz

        sdx -= round(sdx)
        sdy -= round(sdy)
        sdz -= round(sdz)
            
        rx = sdx*cell[0, 0] + sdy*cell[0, 1] + sdz*cell[0, 2]
        ry = sdx*cell[1, 0] + sdy*cell[1, 1] + sdz*cell[1, 2]
        rz = sdx*cell[2, 0] + sdy*cell[2, 1] + sdz*cell[2, 2]

        r2 = rx*rx + ry*ry + rz*rz

        if r2 >= mini2 and r2 <= maxi2:
            indexes.append(i)

    return indexes
            
def atoms_in_shell_nopbc(ndarray[np.float64_t, ndim=2]  config not None,
                         int refIndex,
                         float mini,
                         float maxi):

    cdef double x, y, z, refx, refy, refz, sdx, sdy, sdz, rx, ry, rz, r2

    cdef int i

    refx = config[refIndex,0]
    refy = config[refIndex,1]
    refz = config[refIndex,2]

    cdef double mini2 = mini**2
    cdef double maxi2 = maxi**2

    indexes = []

    for 0 <= i < config.shape[0]:

        if i == refIndex:
            continue

        rx = config[i,0] - refx
        ry = config[i,1] - refy
        rz = config[i,2] - refz
            
        r2 = rx*rx + ry*ry + rz*rz

        if r2 >= mini2 and r2 <= maxi2:
            indexes.append(i)

    return indexes

def atoms_in_shell_box(ndarray[np.float64_t, ndim=2]  config not None,
                       int refIndex,
                       float mini,
                       float maxi):

    cdef double x, y, z, refx, refy, refz, sdx, sdy, sdz, r2

    cdef int i

    cdef double mini2 = mini**2
    cdef double maxi2 = maxi**2

    refx = config[refIndex,0]
    refy = config[refIndex,1]
    refz = config[refIndex,2]

    indexes = []

    for 0 <= i < config.shape[0]:

        if i == refIndex:
            continue

        sdx = config[i,0] - refx
        sdy = config[i,1] - refy
        sdz = config[i,2] - refz

        sdx -= round(sdx)
        sdy -= round(sdy)
        sdz -= round(sdz)
            
        r2 = sdx*sdx + sdy*sdy + sdz*sdz

        if r2 >= mini2 and r2 <= maxi2:
            indexes.append(i)

    return indexes
