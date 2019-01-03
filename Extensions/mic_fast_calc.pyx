# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/mic_fast_calc.pyx
# @brief     Implements module/class/test mic_fast_calc
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

cimport numpy as np 
import numpy as np
from numpy cimport ndarray

from libcpp.vector cimport vector
from libcpp.pair cimport pair 
from libcpp cimport bool

ctypedef pair[ int, vector[int] ] equiv_t
ctypedef vector[double] point

cdef inline bool exclude_from_bounded_3Dbox(double x,
                                            double y,
                                            double z, 
                                            double Xmin, 
                                            double Xmax, 
                                            double Ymin, 
                                            double Ymax, 
                                            double Zmin, 
                                            double Zmax, 
                                            double border): 
    return not ((Xmin-border <=x) and  (x <= Xmax+border) and (Ymin-border <= y) and (y <= Ymax+border) and (Zmin-border <= z) and (z <= Zmax+border)) 

cdef inline bool exclude_from_bounded_2Dbox(double x,
                                            double y,
                                            double Xmin, 
                                            double Xmax, 
                                            double Ymin, 
                                            double Ymax, 
                                            double border): 
    return not ((Xmin-border <=x) and  (x <= Xmax+border) and (Ymin-border <= y) and (y <= Ymax+border))


 
def mic_generator_2D(double[:,:] pts not None, double border, double[:] box_param):

    cdef int i, m, new_id, nb_init_points, nb_final_points
    cdef double x, y, Xmin, Xmax, Ymin, Ymax, j, k, n0, n1
    cdef vector[equiv_t] equivalence
    cdef vector[point] new_points
    cdef equiv_t e
    cdef point n
    cdef double lol[3]
    cdef ndarray[np.float64_t, ndim = 2] res
    
    nb_init_points = pts.shape[0]
    
    Xmax = box_param[0]
    Ymax = box_param[1]
    Xmin = 0
    Ymin = 0 
    
    lol[0] = -1
    lol[1] = 0
    lol[2] = 1
    
    for i in range(nb_init_points):
        x = pts[i,0]
        y = pts[i,1]
        for j in lol[0:3]:
            for k in lol[0:3]:
                if j == 0 and k == 0:
                    continue
                n0 = x+j*(Xmax-Xmin)
                n1 = y+k*(Ymax-Ymin)
                
                if exclude_from_bounded_2Dbox(n0, n1, Xmin, Xmax, Ymin, Ymax, border):
                    continue
                n = point()
                n.push_back(n0)
                n.push_back(n1)
                new_points.push_back(n)
                new_id = new_points.size() + nb_init_points
                for m in range(equivalence.size()):
                    if equivalence[m].first == i:
                        equivalence[m].second.push_back(new_id)
                        continue
                    e = equiv_t()
                    e.first=i
                    e.second.push_back(new_id)
                    equivalence.push_back(e)
    d = {}
    for i in range(equivalence.size()):
        d[equivalence[i].first] = <list> equivalence[i].second
        
    nb_final_points = pts.shape[0] + new_points.size()
    
    res = np.zeros((nb_init_points + new_points.size() ,2), dtype = np.float64)

    for i in range(nb_init_points):
        res[i,0] = pts[i,0]
        res[i,1] = pts[i,1]
    
    for i in range(new_points.size()):
        j = i + nb_init_points
        res[j,0] = new_points[i][0]
        res[j,1] = new_points[i][1]
    
    
    return res, d

        
        
def mic_generator_3D(double[:,:] pts not None, double border, double[:] box_param):
    
    cdef int i, j_int, m, new_id, nb_init_points
    cdef double x, y, z, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, j, k, l, n0, n1, n2
    cdef vector[equiv_t] equivalence
    cdef vector[point] new_points
    cdef equiv_t e
    cdef point n
    cdef double lol[3]
    cdef ndarray[np.float64_t, ndim = 2] res
    
    nb_init_points = pts.shape[0]
    
    Xmax = box_param[0]
    Ymax = box_param[1]
    Zmax = box_param[2] 
    Xmin = 0
    Ymin = 0 
    Zmin = 0

    lol[0] = -1
    lol[1] = 0
    lol[2] = 1
    
    for i in range(nb_init_points):
        x = pts[i,0]
        y = pts[i,1]
        z = pts[i,2]
        for j in lol[0:3]:
            for k in lol[0:3]:
                for l in lol[0:3]:
                    if j == 0 and k == 0 and l == 0:
                        continue
                    n0 = x+j*(Xmax-Xmin)
                    n1 = y+k*(Ymax-Ymin)
                    n2 = z+l*(Zmax-Zmin)
                    
                    if exclude_from_bounded_3Dbox(n0, n1, n2, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, border):
                        continue
                    n = point()
                    n.push_back(n0)
                    n.push_back(n1)
                    n.push_back(n2)
                    new_points.push_back(n)
                    new_id = new_points.size() + nb_init_points
                    for m in range(equivalence.size()):
                        if equivalence[m].first == i:
                            equivalence[m].second.push_back(new_id)
                            continue
                        e = equiv_t()
                        e.first=i
                        e.second.push_back(new_id)
                        equivalence.push_back(e)

    d = {}
    for i in range(equivalence.size()):
        d[equivalence[i].first] = <list> equivalence[i].second

    res = np.zeros((nb_init_points + new_points.size() ,3), dtype = np.float64)

    for i in range(nb_init_points):
        res[i,0] = pts[i,0]
        res[i,1] = pts[i,1]
        res[i,2] = pts[i,2]
    
    for i in range(new_points.size()):
        j = i + nb_init_points
        j_int = int(j)
        res[j_int,0] = new_points[i][0]
        res[j_int,1] = new_points[i][1]
        res[j_int,2] = new_points[i][2]
    
    return res, d
