'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

import numpy

from MDANSE.Core.Error import Error
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.Signal import correlation

class AnalysisError(Error):
    pass
                                              
def mean_square_deviation(coords1, coords2, masses=None, root=False):
    """Computes the mean square deviation between two sets of coordinates 
    :Parameters:
        #. coords1 ((n,3)-numpy.array): the first set of coordinates
        #. coords2 ((n,3)-numpy.array): the second set of coordinates
        #. masses  ((n, )-numpy.array): the input masses
        #. root    bool: if True, return the square root of the mean square deviation (the so-called RMSD)
    :Returns:
        #. float: the radius of gyration
    """

    if coords1.shape != coords2.shape:
        raise AnalysisError("The input coordinates shapes do not match")

    if masses is None:
        masses = numpy.ones((coords1.shape[0]),dtype=numpy.float64)

    rmsd = numpy.sum(numpy.sum((coords1-coords2)**2,axis=1)*masses)/numpy.sum(masses)

    if root:
        rmsd = numpy.sqrt(rmsd)
    
    return rmsd

def mean_square_displacement(coordinates):
    
    dsq = numpy.add.reduce(coordinates**2,1)

    # sum_dsq1 is the cumulative sum of dsq
    sum_dsq1 = numpy.add.accumulate(dsq)

    # sum_dsq1 is the reversed cumulative sum of dsq
    sum_dsq2 = numpy.add.accumulate(dsq[::-1])

    # sumsq refers to SUMSQ in the published algorithm
    sumsq = 2.0*sum_dsq1[-1]

    # this line refers to the instruction SUMSQ <-- SUMSQ - DSQ(m-1) - DSQ(N - m) of the published algorithm
    # In this case, msd is an array because the instruction is computed for each m ranging from 0 to len(traj) - 1
    # So, this single instruction is performing the loop in the published algorithm
    Saabb  = sumsq - numpy.concatenate(([0.0], sum_dsq1[:-1])) - numpy.concatenate(([0.0], sum_dsq2[:-1]))

    # Saabb refers to SAA+BB/(N-m) in the published algorithm
    # Sab refers to SAB(m)/(N-m) in the published algorithm
    Saabb = Saabb / (len(dsq) - numpy.arange(len(dsq)))
    Sab   = 2.0*correlation(coordinates, axis=0, reduce=1)

    # The atomic MSD.
    msd = Saabb - Sab
                            
    return msd

def mean_square_fluctuation(coords, root=False):
    
    msf = numpy.average(numpy.sum((coords-numpy.average(coords,axis=0))**2,axis=1))
    
    if root:
        msf = numpy.sqrt(msf)
        
    return msf    

def radius_of_gyration(coords, masses=None, root=False):
    """Computes the radius of gyration for a set of coordinates
    :Parameters:
        #. coords  ((n,3)-numpy.array): the set of  coordinates
        #. masses  ((n, )-numpy.array): the input masses
        #. root    bool: if True, return the square root of the radius of gyration
    :Returns:
        #. float: the radius of gyration
    """
    
    if masses is None:
        masses = numpy.ones((coords.shape[0]),dtype=numpy.float64)
            
    com = center_of_mass(coords,masses)
        
    rog = numpy.sum(numpy.sum((coords-com)**2,axis=1)*masses)/numpy.sum(masses)
    
    if root:
        rog = numpy.sqrt(rog)
        
    return rog

