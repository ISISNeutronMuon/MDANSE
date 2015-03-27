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
    
    cdef int at, nbatom , atom
    cdef double Xpos, Ypos, Zpos, i, j, k , mx, my, mz
    
    mx = mini[0] 
    my = mini[1]
    mz = mini[2]
    
    nbatom = config.shape[0]
    for atom in range(nbatom):
        # The  of atoms |i| in the current configuration.
        i = floor((config[atom,0]-mx)/resolution)
        j = floor((config[atom,1]-my)/resolution)
        k = floor((config[atom,2]-mz)/resolution)
        grid[i,j,k] += 1
