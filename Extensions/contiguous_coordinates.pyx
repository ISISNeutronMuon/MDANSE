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

import sys

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

def contiguous_coordinates_real(ndarray[np.float64_t, ndim=2] coords not None,
                                ndarray[np.float64_t, ndim=2] cell not None,
                                ndarray[np.float64_t, ndim=2] rcell not None,
                                indexes):

    cdef double x, y, z, sdx, sdy, sdz, newx, newy, newz

    cdef int i


    cdef ndarray[np.float64_t, ndim=2] contiguous_coords = np.empty((coords.shape[0],3),dtype=np.float)

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((coords.shape[0],3),dtype=np.float)

    for 0 <= i < coords.shape[0]:

        x = coords[i,0]
        y = coords[i,1]
        z = coords[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    for idxs in indexes:

        if not idxs:
            continue
            
        contiguous_coords[idxs[0],0] = coords[idxs[0],0]
        contiguous_coords[idxs[0],1] = coords[idxs[0],1]
        contiguous_coords[idxs[0],2] = coords[idxs[0],2]

        if len(idxs) == 1:
            continue

        for idx in idxs[1:]:

            sdx = scaleconfig[idx,0] - scaleconfig[idxs[0],0]
            sdy = scaleconfig[idx,1] - scaleconfig[idxs[0],1]
            sdz = scaleconfig[idx,2] - scaleconfig[idxs[0],2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            newx = scaleconfig[idxs[0],0] + sdx
            newy = scaleconfig[idxs[0],1] + sdy
            newz = scaleconfig[idxs[0],2] + sdz

            contiguous_coords[idx,0] = newx*cell[0,0] + newy*cell[0,1] + newz*cell[0,2]
            contiguous_coords[idx,1] = newx*cell[1,0] + newy*cell[1,1] + newz*cell[1,2]
            contiguous_coords[idx,2] = newx*cell[2,0] + newy*cell[2,1] + newz*cell[2,2]

    return contiguous_coords

def contiguous_coordinates_box(ndarray[np.float64_t, ndim=2]  coords not None,
                               ndarray[np.float64_t, ndim=2]  cell not None,
                               indexes):

    cdef double sdx, sdy, sdz, newx, newy, newz

    cdef ndarray[np.float64_t, ndim=2] contiguous_coords = np.empty((coords.shape[0],3), dtype=np.float64)

    for idxs in indexes:
        contiguous_coords[idxs[0], 0] = coords[idxs[0], 0]
        contiguous_coords[idxs[0], 1] = coords[idxs[0], 1]
        contiguous_coords[idxs[0], 2] = coords[idxs[0], 2]

        if len(idxs) == 1:
            continue

        for idx in idxs[1:]:

            sdx = coords[idx, 0] - coords[idxs[0], 0]
            sdy = coords[idx, 1] - coords[idxs[0], 1]
            sdz = coords[idx, 2] - coords[idxs[0], 2]

            sdx -= round(sdx)
            sdy -= round(sdy)
            sdz -= round(sdz)

            newx = coords[idxs[0], 0] + sdx
            newy = coords[idxs[0], 1] + sdy
            newz = coords[idxs[0], 2] + sdz

            contiguous_coords[idx, 0] = newx*cell[0, 0] + newy*cell[0, 1] + newz*cell[0, 2]
            contiguous_coords[idx, 1] = newx*cell[1, 0] + newy*cell[1, 1] + newz*cell[1, 2]
            contiguous_coords[idx, 2] = newx*cell[2, 0] + newy*cell[2, 1] + newz*cell[2, 2]

    return contiguous_coords

def contiguous_offsets_real(ndarray[np.float64_t, ndim=2]  coords not None,
                            ndarray[np.float64_t, ndim=2]  cell not None,
                            ndarray[np.float64_t, ndim=2]  rcell not None,
                            indexes):

    cdef double x, y, z, sdx, sdy, sdz

    cdef int i

    cdef ndarray[np.float64_t, ndim=2] scaleconfig = np.empty((coords.shape[0],3),dtype=np.float)

    cdef ndarray[np.float64_t, ndim=2] offsets = np.zeros((coords.shape[0],3),dtype=np.float)

    for 0 <= i < coords.shape[0]:

        x = coords[i,0]
        y = coords[i,1]
        z = coords[i,2]

        scaleconfig[i,0] = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        scaleconfig[i,1] = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        scaleconfig[i,2] = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

    for idxs in indexes:
        if len(idxs) == 1:
            continue
        
        for idx in idxs[1:]:

            sdx = scaleconfig[idx,0] - scaleconfig[idxs[0],0]
            sdy = scaleconfig[idx,1] - scaleconfig[idxs[0],1]
            sdz = scaleconfig[idx,2] - scaleconfig[idxs[0],2]

            offsets[idx,0] = -round(sdx)
            offsets[idx,1] = -round(sdy)
            offsets[idx,2] = -round(sdz)

    return offsets

def contiguous_offsets_box(ndarray[np.float64_t, ndim=2]  coords not None,
                           ndarray[np.float64_t, ndim=2]  cell not None,
                           indexes):

    cdef double sdx, sdy, sdz

    cdef ndarray[np.float64_t, ndim=2] offsets = np.zeros((coords.shape[0], 3), dtype=np.float64)

    for idxs in indexes:
        if len(idxs) == 1:
            continue
        
        for idx in idxs[1:]:

            sdx = coords[idx, 0] - coords[idxs[0], 0]
            sdy = coords[idx, 1] - coords[idxs[0], 1]
            sdz = coords[idx, 2] - coords[idxs[0], 2]

            offsets[idx, 0] = -round(sdx)
            offsets[idx, 1] = -round(sdy)
            offsets[idx, 2] = -round(sdz)

    return offsets

def _recursive_contiguity(
    ndarray[np.float64_t, ndim=2] contiguous_coords,
    ndarray[np.float64_t, ndim=2] cell not None,
    ndarray[np.float64_t, ndim=2] rcell not None,
    ndarray[np.int8_t, ndim=1] processed not None,
    bonds,
    seed):

    cdef double refx, refy, refz, brefx, brefy, brefz,x, y, z, bx, by, bz, bdx, bdy, bdz

    # The seed atom is marked as processed
    processed[seed] = 1

    # Convert from real to box coordinates for the seed atom
    refx = contiguous_coords[seed,0]
    refy = contiguous_coords[seed,1]
    refz = contiguous_coords[seed,2]

    brefx = refx*rcell[0,0] + refy*rcell[0,1] + refz*rcell[0,2]
    brefy = refx*rcell[1,0] + refy*rcell[1,1] + refz*rcell[1,2]
    brefz = refx*rcell[2,0] + refy*rcell[2,1] + refz*rcell[2,2]

    bonded_atoms = bonds[seed]

    # Loop over the atoms bonded to the seed
    for bat in bonded_atoms:

        # If the bonded atom is marked as processed skip it
        if processed[bat] == 1:
            continue

        # Convert from real to box coordinates for the bonded atom
        x = contiguous_coords[bat,0]
        y = contiguous_coords[bat,1]
        z = contiguous_coords[bat,2]

        bx = x*rcell[0,0] + y*rcell[0,1] + z*rcell[0,2]
        by = x*rcell[1,0] + y*rcell[1,1] + z*rcell[1,2]
        bz = x*rcell[2,0] + y*rcell[2,1] + z*rcell[2,2]

        # Apply the PBC
        bdx = bx - brefx
        bdy = by - brefy
        bdz = bz - brefz

        bdx -= round(bdx)
        bdy -= round(bdy)
        bdz -= round(bdz)

        bx = brefx + bdx
        by = brefy + bdy
        bz = brefz + bdz

        # Convert back from box to real coordinates
        contiguous_coords[bat,0] = bx*cell[0,0] + by*cell[0,1] + bz*cell[0,2]
        contiguous_coords[bat,1] = bx*cell[1,0] + by*cell[1,1] + bz*cell[1,2]
        contiguous_coords[bat,2] = bx*cell[2,0] + by*cell[2,1] + bz*cell[2,2]

        _recursive_contiguity(contiguous_coords,cell,rcell,processed,bonds,bat)

def continuous_coordinates(
    ndarray[np.float64_t, ndim=2] coords not None,
    ndarray[np.float64_t, ndim=2] cell not None,
    ndarray[np.float64_t, ndim=2] rcell not None,
    chemical_system,
    selected_indexes=None):

    cdef int ref_idx

    cdef ndarray[np.float64_t, ndim=2] continuous_coords = coords

    cdef np.ndarray[np.int8_t] processed = np.zeros((coords.shape[0],), dtype=np.int8)

    old_recursionlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(100000)

    # Retrieve the top level chemical entities to which belong each of the selected atom
    atoms = chemical_system.atom_list()
    if selected_indexes is None:
        selected_indexes = [at.index for at in atoms]

    chemical_entities = set([atoms[idx].top_level_chemical_entity() for idx in selected_indexes])

    # Set the bond network for these chemical entities
    bonds = {}
    chemical_entities_indexes = []
    for ce in chemical_entities:
        for at in ce.atom_list():
            bonds[at.index] = [bat.index for bat in at.bonds]
            chemical_entities_indexes.append(at.index)

    chemical_entities_indexes.sort()

    for idx in chemical_entities_indexes:

        _recursive_contiguity(continuous_coords, cell, rcell, processed, bonds, idx)

    sys.setrecursionlimit(old_recursionlimit)

    return continuous_coords[selected_indexes,:]








            
