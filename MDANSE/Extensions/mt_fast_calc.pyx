
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
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import cython
cimport numpy as np 
import numpy as np
from numpy cimport ndarray

cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)

@cython.boundscheck(False)
@cython.wraparound(False)
def mt(ndarray[np.float64_t, ndim = 2] config not None,
       ndarray[np.int32_t, ndim = 3] grid not None,
       double resolution,ndarray[np.float64_t, ndim = 1] mini not None): 
    
    cdef int at, nbatom, atom, i, j, k
    cdef double Xpos, Ypos, Zpos, mx, my, mz
    
    mx = mini[0] 
    my = mini[1]
    mz = mini[2]
    
    nbatom = config.shape[0]
    for atom in range(nbatom):
        # The  of atoms |i| in the current configuration.
        i = int(floor((config[atom,0]-mx)/resolution))
        j = int(floor((config[atom,1]-my)/resolution))
        k = int(floor((config[atom,2]-mz)/resolution))
        grid[i][j][k] += 1
