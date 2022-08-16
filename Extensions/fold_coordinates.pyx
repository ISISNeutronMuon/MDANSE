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

def fold_coordinates(
    ndarray[np.float64_t, ndim=3] coords not None,
    cells,
    rcells,
    box_coordinates=True):

    cdef double x, y, z, bx, by, bz

    cdef int i

    cdef ndarray[np.float64_t, ndim=3] folded_coords = np.empty((coords.shape[0],coords.shape[1],3),dtype=np.float64)

    cdef ndarray[np.float64_t, ndim=3] box_coords

    if cells is None:

        return coords

    if not box_coordinates:

        box_coords = np.empty((coords.shape[0],coords.shape[1],3),dtype=np.float64)

        for 0 <= i < box_coords.shape[0]:

            for 0 <= j < box_coords.shape[1]:

                x = coords[i,j,0]
                y = coords[i,j,1]
                z = coords[i,j,2]

                # Convert the real coordinates to box coordinates
                box_coords[i,j,0] = x*rcells[i,0,0] + y*rcells[i,0,1] + z*rcells[i,0,2]
                box_coords[i,j,1] = x*rcells[i,1,0] + y*rcells[i,1,1] + z*rcells[i,1,2]
                box_coords[i,j,2] = x*rcells[i,2,0] + y*rcells[i,2,1] + z*rcells[i,2,2]

    else:

        box_coords = coords


    for 0 <= i < box_coords.shape[0]:

        for 0 <= j < box_coords.shape[1]:

            bx = box_coords[i,j,0]
            by = box_coords[i,j,1]
            bz = box_coords[i,j,2]
    
            while bx < -0.5:
                bx += 1.0

            while by < -0.5:
                by += 1.0

            while bz < -0.5:
                bz += 1.0

            while bx > 0.5:
                bx -= 1.0

            while by > 0.5:
                by -= 1.0

            while bz > 0.5:
                bz -= 1.0

            box_coords[i,j,0] = bx
            box_coords[i,j,1] = by
            box_coords[i,j,2] = bz

    if not box_coordinates:

        for 0 <= i < box_coords.shape[0]:

            for 0 <= j < box_coords.shape[1]:

                x = box_coords[i,j,0]
                y = box_coords[i,j,1]
                z = box_coords[i,j,2]

                folded_coords[i,j,0] = x*cells[i,0,0] + y*cells[i,0,1] + z*cells[i,0,2]
                folded_coords[i,j,1] = x*cells[i,1,0] + y*cells[i,1,1] + z*cells[i,1,2]
                folded_coords[i,j,2] = x*cells[i,2,0] + y*cells[i,2,1] + z*cells[i,2,2]

    else:

        folded_coords = box_coords

    return folded_coords
