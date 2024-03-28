
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

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def atomic_trajectory(
    ndarray[np.float64_t, ndim=2] config not None,
    ndarray[np.float64_t, ndim=3] cell not None,
    ndarray[np.float64_t, ndim=3] rcell not None,
    box_coordinates = False):

    cdef double x, y, z, refx, refy, refz, sdx, sdy, sdz

    cdef int i, j

    cdef ndarray[np.float64_t, ndim=2] trajectory = np.empty((config.shape[0],3),dtype=np.float64)

    # Loop over the time
    for 0 <= i < config.shape[0]:

        # The first atom is taken as reference
        refx = config[i,0]
        refy = config[i,1]
        refz = config[i,2]

        trajectory[i,0] = refx*rcell[i,0,0] + refy*rcell[i,0,1] + refz*rcell[i,0,2]
        trajectory[i,1] = refx*rcell[i,1,0] + refy*rcell[i,1,1] + refz*rcell[i,1,2]
        trajectory[i,2] = refx*rcell[i,2,0] + refy*rcell[i,2,1] + refz*rcell[i,2,2]

        if i > 0:

            sdx = trajectory[i,0] - trajectory[i-1,0]
            sdy = trajectory[i,1] - trajectory[i-1,1]
            sdz = trajectory[i,2] - trajectory[i-1,2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            trajectory[i,0] = trajectory[i-1,0] + sdx
            trajectory[i,1] = trajectory[i-1,1] + sdy
            trajectory[i,2] = trajectory[i-1,2] + sdz

    if not box_coordinates:

        for 0 <= i < config.shape[0]:
            x = trajectory[i,0]
            y = trajectory[i,1]
            z = trajectory[i,2]
            
            trajectory[i,0] = x*cell[i,0,0] + y*cell[i,0,1] + z*cell[i,0,2]
            trajectory[i,1] = x*cell[i,1,0] + y*cell[i,1,1] + z*cell[i,1,2]
            trajectory[i,2] = x*cell[i,2,0] + y*cell[i,2,1] + z*cell[i,2,2]

    return trajectory

