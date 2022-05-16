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

def _recursive_contiguity(
    ndarray[np.float64_t, ndim=2] contiguous_coords,
    ndarray[np.float64_t, ndim=2] cell not None,
    ndarray[np.float64_t, ndim=2] rcell not None,
    ndarray[np.int8_t, ndim=1] processed not None,
    bonds,
    ref):

    cdef double refx, refy, refz, brefx, brefy, brefz,x, y, z, bx, by, bz, bdx, bdy, bdz

    refx = contiguous_coords[ref,0]
    refy = contiguous_coords[ref,1]
    refz = contiguous_coords[ref,2]

    brefx = refx*rcell[0,0] + refy*rcell[0,1] + refz*rcell[0,2]
    brefy = refx*rcell[1,0] + refy*rcell[1,1] + refz*rcell[1,2]
    brefz = refx*rcell[2,0] + refy*rcell[2,1] + refz*rcell[2,2]

    bonded_atoms = bonds[ref]

    processed[ref] = 1

    for bat in bonded_atoms:

        if processed[bat] == 1:
            continue

        x = contiguous_coords[bat,0]
        y = contiguous_coords[bat,1]
        z = contiguous_coords[bat,2]

        bx = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        by = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        bz = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

        bdx = bx - brefx
        bdy = by - brefy
        bdz = bz - brefz

        bdx -= round(bdx)
        bdy -= round(bdy)
        bdz -= round(bdz)

        bx = brefx + bdx
        by = brefy + bdy
        bz = brefz + bdz

        contiguous_coords[bat,0] = bx*cell[0,0] + by*cell[0,1] + bz*cell[0,2]
        contiguous_coords[bat,1] = bx*cell[1,0] + by*cell[1,1] + bz*cell[1,2]
        contiguous_coords[bat,2] = bx*cell[2,0] + by*cell[2,1] + bz*cell[2,2]

        _recursive_contiguity(contiguous_coords,cell,rcell,processed, bonds, bat)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def com_trajectory(
    ndarray[np.float64_t, ndim=3] coords not None,
    ndarray[np.float64_t, ndim=3] cell not None,
    ndarray[np.float64_t, ndim=3] rcell not None,
    ndarray[np.float64_t, ndim=1] masses not None,
    chemical_entity_indexes,
    selected_indexes,
    bonds,
    box_coordinates = False):

    cdef double x, y, z, refx, refy, refz, \
                srefx, srefy, srefz, sx, sy, sz, sdx, sdy, sdz, \
                sumMasses, comx, comy, comz, refcomx, refcomy, refcomz

    cdef int i, j

    cdef ndarray[np.float64_t, ndim=2] trajectory = np.empty((coords.shape[0],3),dtype=np.float)

    cdef ndarray[np.float64_t, ndim=2] continuous_coords

    cdef np.ndarray[np.int8_t] processed

    # Loop over the time
    for 0 <= i < coords.shape[0]:

        continuous_coords = coords[i,:,:]

        processed = np.zeros((continuous_coords.shape[0],), dtype=np.int8)

        for idxs in chemical_entity_indexes:

            if len(idxs) > 1:
                ref_idx = idxs.pop(0)
                _recursive_contiguity(continuous_coords, cell[i,:,:], rcell[i,:,:], processed, bonds, ref_idx)

        # The first atom is taken as reference
        refx = continuous_coords[selected_indexes[0],0]
        refy = continuous_coords[selected_indexes[0],1]
        refz = continuous_coords[selected_indexes[0],2]

        srefx = refx*rcell[i,0,0] + refy*rcell[i,0,1] + refz*rcell[i,0,2]
        srefy = refx*rcell[i,1,0] + refy*rcell[i,1,1] + refz*rcell[i,1,2]
        srefz = refx*rcell[i,2,0] + refy*rcell[i,2,1] + refz*rcell[i,2,2]

        comx = masses[0]*srefx
        comy = masses[0]*srefy
        comz = masses[0]*srefz

        sumMasses = masses[0]

        # Loop over the atoms
        for j in range(1,len(selected_indexes)):

            idx = selected_indexes[j]

            x = continuous_coords[idx,0]
            y = continuous_coords[idx,1]
            z = continuous_coords[idx,2]

            sx = x*rcell[i,0,0] + y*rcell[i,0,1] + z*rcell[i,0,2]
            sy = x*rcell[i,1,0] + y*rcell[i,1,1] + z*rcell[i,1,2]
            sz = x*rcell[i,2,0] + y*rcell[i,2,1] + z*rcell[i,2,2]

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

    return trajectory

