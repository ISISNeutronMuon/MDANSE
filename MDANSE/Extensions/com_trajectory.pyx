
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

import sys

import cython
import numpy as np 
cimport numpy as np 

cdef extern from "math.h":

    double floor(double x)
    double ceil(double x)
    double sqrt(double x)

cdef inline double round(double r):
    return floor(r + 0.5) if (r > 0.0) else ceil(r - 0.5)

def _recursive_contiguity(
    np.ndarray[np.float64_t, ndim=2] box_coords,
    np.ndarray[np.int8_t, ndim=1] processed not None,
    bonds,
    ref):

    cdef int bat

    cdef double brefx, brefy, brefz, bx, by, bz, bdx, bdy, bdz

    brefx = box_coords[ref,0]
    brefy = box_coords[ref,1]
    brefz = box_coords[ref,2]

    bonded_atoms = bonds[ref]

    processed[ref] = 1

    for bat in bonded_atoms:

        if processed[bat] == 1:
            continue

        bx = box_coords[bat,0]
        by = box_coords[bat,1]
        bz = box_coords[bat,2]

        bdx = bx - brefx
        bdy = by - brefy
        bdz = bz - brefz

        bdx -= round(bdx)
        bdy -= round(bdy)
        bdz -= round(bdz)

        bx = brefx + bdx
        by = brefy + bdy
        bz = brefz + bdz

        box_coords[bat,0] = bx
        box_coords[bat,1] = by
        box_coords[bat,2] = bz

        _recursive_contiguity(box_coords,processed, bonds, bat)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def com_trajectory(
    np.ndarray[np.float64_t, ndim=3] coords not None,
    np.ndarray[np.float64_t, ndim=3] cell not None,
    np.ndarray[np.float64_t, ndim=3] rcell not None,
    np.ndarray[np.float64_t, ndim=1] masses not None,
    chemical_entity_indexes,
    selected_indexes,
    bonds,
    box_coordinates = False):

    cdef double x, y, z, refx, refy, refz, \
                srefx, srefy, srefz, sx, sy, sz, sdx, sdy, sdz, \
                sumMasses, comx, comy, comz

    cdef int i, j, idx, idx0

    cdef np.ndarray[np.float64_t, ndim=2] trajectory = np.empty((coords.shape[0],3),dtype=np.float64)

    cdef np.ndarray[np.float64_t, ndim=2] com_coords

    cdef np.ndarray[np.int8_t] processed

    cdef np.ndarray[np.float64_t, ndim=3] box_coords = np.empty((coords.shape[0],coords.shape[1],3),dtype=np.float64)


    old_recursionlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(100000)

    # Loop over the time
    for 0 <= i < coords.shape[0]:

        # Loop over the atoms
        for 0 <= j < coords.shape[1]:

            x = coords[i,j,0]
            y = coords[i,j,1]
            z = coords[i,j,2]

            # Convert the real coordinates to box coordinates
            box_coords[i,j,0] = x*rcell[i,0,0] + y*rcell[i,0,1] + z*rcell[i,0,2]
            box_coords[i,j,1] = x*rcell[i,1,0] + y*rcell[i,1,1] + z*rcell[i,1,2]
            box_coords[i,j,2] = x*rcell[i,2,0] + y*rcell[i,2,1] + z*rcell[i,2,2]

    # Loop over the time
    for 0 <= i < coords.shape[0]:

        com_coords = box_coords[i,:,:]

        processed = np.zeros((com_coords.shape[0],), dtype=np.int8)

        for idxs in chemical_entity_indexes:

            if len(idxs) > 1:
                ref_idx = idxs.pop(0)
                _recursive_contiguity(com_coords, processed, bonds, ref_idx)

        idx0 = selected_indexes[0]

        # The first atom is taken as reference
        srefx = com_coords[idx0,0]
        srefy = com_coords[idx0,1]
        srefz = com_coords[idx0,2]

        comx = masses[0]*srefx
        comy = masses[0]*srefy
        comz = masses[0]*srefz

        sumMasses = masses[0]

        # Loop over the other atoms (if any)
        for j in range(1,len(selected_indexes)):

            idx = selected_indexes[j]

            sx = com_coords[idx,0]
            sy = com_coords[idx,1]
            sz = com_coords[idx,2]

            # Update the center of mass
            comx += masses[j]*sx
            comy += masses[j]*sy
            comz += masses[j]*sz

            sumMasses += masses[j]

        if i == 0:

            trajectory[i,0] = comx/sumMasses
            trajectory[i,1] = comy/sumMasses
            trajectory[i,2] = comz/sumMasses

        # The step i-1 is taken as the reference
        else:

            comx /= sumMasses
            comy /= sumMasses
            comz /= sumMasses

            sdx = comx - trajectory[i-1,0]
            sdy = comy - trajectory[i-1,1]
            sdz = comz - trajectory[i-1,2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            trajectory[i,0] = trajectory[i-1,0] + sdx
            trajectory[i,1] = trajectory[i-1,1] + sdy
            trajectory[i,2] = trajectory[i-1,2] + sdz

    if not box_coordinates:

        for 0 <= i < trajectory.shape[0]:

            x = trajectory[i,0]
            y = trajectory[i,1]
            z = trajectory[i,2]

            trajectory[i,0] = x*cell[i,0,0] + y*cell[i,0,1] + z*cell[i,0,2]
            trajectory[i,1] = x*cell[i,1,0] + y*cell[i,1,1] + z*cell[i,1,2]
            trajectory[i,2] = x*cell[i,2,0] + y*cell[i,2,1] + z*cell[i,2,2]

    sys.setrecursionlimit(old_recursionlimit)

    return trajectory

