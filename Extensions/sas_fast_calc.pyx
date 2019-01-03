# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/sas_fast_calc.pyx
# @brief     Implements module/class/test sas_fast_calc
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
import numpy as np
cimport numpy as np 
from numpy cimport ndarray
from libc.string cimport memset

cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)
    double sqrt(double x)

cdef packed struct neighbour_t:
    np.int32_t index
    np.float64_t dist

@cython.boundscheck(False)
@cython.wraparound(False)
def sas(int index,
        ndarray[np.float64_t, ndim = 2] config not None,
        ndarray[np.int32_t, ndim = 1] indexes not None,
        ndarray[np.float64_t, ndim = 2] vdwRadii_list not None,
        ndarray[np.float64_t, ndim = 2] sphere_points not None,
        double probe_radius_value): 

    # Computes the Solvent Accessible Surface Based on the algorithm published by Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371. 
    
    cdef int total, i, j, k, n, isAccessible, nAccessiblePoints
    cdef double sas, dist, v, radi, r, radius, two_times_prob_radius
    cdef double Xposi, Yposi, Zposi, Xposj, Yposj, Zposj, Xposk, Yposk, Zposk, Xs, Ys, Zs, Xguess, Yguess, Zguess, dx, dy, dz
    
    # The solvent accessible surface for the running frame (given by index var).
    total = len(indexes)
    
    # The list of the neighbors indexes. 
    neighbour_dtype=[("index",np.int32),("dist",np.float64)]
    
    cdef np.ndarray[neighbour_t, ndim = 1] neighbors = np.recarray(shape=(total ,),dtype=neighbour_dtype)
    memset(&neighbors[0], -1, total *sizeof(neighbour_t))
    
    sas = 0.
    two_times_prob_radius = 2.0*probe_radius_value
    for i in indexes:
        
        # The position of atoms |i| in the current configuration.
        Xposi = config[i,0]
        Yposi = config[i,1]
        Zposi = config[i,2]
        
        # The probe radius of atom |index|.
        radius = vdwRadii_list[i][1] 
        radius = radius + two_times_prob_radius
        # Loop over all the atoms.
        for item in vdwRadii_list:
            k = item[0]
            v = item[1]
            # Skip the case where the atoms is itself.
            if k == i:
                neighbors[k].index = k
                neighbors[k].dist  = -1
                continue
           
            Xposk = config[k,0]
            Yposk = config[k,1]
            Zposk = config[k,2]
            # ??  identical to -->  dist = self.configuration['trajectory']['instance'].universe.distance(self.atoms[index],self.atoms[k])
            # The distance between atoms |index| and |k|.
            dx = Xposi - Xposk
            dy = Yposi - Yposk
            dz = Zposi - Zposk

            dist = (dx) * (dx) + (dy) * (dy) + (dz) * (dz)       

            # If the distance is less than the probe radius + the VDW radius of atoms |k|, atom |k| is considered to be a neighbor of atom |index|.
            if dist < (radius + v)*(radius + v):
                neighbors[k].index = k
                neighbors[k].dist  = v
            else:
                neighbors[k].index = k
                neighbors[k].dist = -1.
                
        
        # Sort the neighbors by increasing distance. -> not usefull ? cost of the sort / cost to parse the full list
        neighbors.sort(order = 'dist')
        # The probe radius of atoms |i|.
        radi = radius + probe_radius_value

        # A counter for the number of atoms |i| sphere points accessible to solvent.
        nAccessiblePoints = 0
            
        # Loop over the sphere points surrounding atoms |i|.\
        nb_neighbors = neighbors.shape[0] 
        for Spoint in sphere_points:
        
            # The running point is first considered to be accessible.
            isAccessible = True
            Xs = Spoint[0]
            Ys = Spoint[1]
            Zs = Spoint[2]
            # Build the sphere point vector.
            Xguess = Xs*radi + Xposi
            Yguess = Ys*radi + Yposi
            Zguess = Zs*radi + Zposi
            
            # Loop over the neighbors of atoms |i|.
            
            for 0 <=  n < nb_neighbors:
                if neighbors[n].dist == -1:
                    continue
                j = neighbors[n].index
                # The position of neighbors |j|.
                Xposj = config[j,0]
                Yposj = config[j,1]
                Zposj = config[j,2]

                # The probe radius of neighbor |j|.
                r = vdwRadii_list[j][1] 
                r = r + probe_radius_value

                # The squared distance between the neighbors |j| and the running sphere point.
                dx = Xposj - Xguess
                dy = Yposj - Yguess
                dz = Zposj - Zguess
                
                dist = (dx) * (dx) + (dy) * (dy) + (dz) * (dz)    

                # If the squared distance is less than the squared probe radius, the running sphere point is not accessible.
                if dist < r*r:
                    isAccessible = False
                    break
                                    
            # Increase the number of accessible point if the running sphere point is found to be accessible.
            if isAccessible:
                nAccessiblePoints += 1

        # Updates the SAS with the contribution for atom |i|.
        sas += nAccessiblePoints*radi*radi 
        # reset neighbors list
        memset(&neighbors[0], -1, total *sizeof(neighbour_t))
        
    return sas