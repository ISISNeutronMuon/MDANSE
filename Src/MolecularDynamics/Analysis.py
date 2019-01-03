import numpy

from MDANSE.Core.Error import Error
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.Signal import correlation

class AnalysisError(Error):
    pass
                                              
def mean_square_deviation(coords1, coords2, masses=None, root=False):
    '''
    Computes the mean square deviation between two sets of coordinates 
    :param coords1: the first set of n coordinates.
    :type coords1: (n,3) numpy array
    :param coords2: the second set of n coordinates.
    :type coords2: (n,3) numpy array
    :param masses: the n input masses. If None the center of gravity is computed.
    :type masses: n-numpy array
    :param root: if True, return the square root of the radius of gyration.
    :type root: bool
    :return: the mean square deviation.
    :rtype: float
    '''

    if coords1.shape != coords2.shape:
        raise AnalysisError("The input coordinates shapes do not match")

    if masses is None:
        masses = numpy.ones((coords1.shape[0]),dtype=numpy.float64)

    rmsd = numpy.sum(numpy.sum((coords1-coords2)**2,axis=1)*masses)/numpy.sum(masses)

    if root:
        rmsd = numpy.sqrt(rmsd)
    
    return rmsd

def mean_square_displacement(coords):
    '''
    Computes the mean square displacement of a set of coordinates 
    :param coords: the set of n coordinates.
    :type coords: (n,3) numpy array
    :return: the mean square displacement.
    :rtype: float
    '''
    
    dsq = numpy.add.reduce(coords**2,1)

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
    Sab   = 2.0*correlation(coords, axis=0, sumOverAxis=1)

    # The atomic MSD.
    msd = Saabb - Sab
                            
    return msd

def mean_square_fluctuation(coords, root=False):
    
    msf = numpy.average(numpy.sum((coords-numpy.average(coords,axis=0))**2,axis=1))
    
    if root:
        msf = numpy.sqrt(msf)
        
    return msf    

def radius_of_gyration(coords, masses=None, root=False):
    '''
    Computes the radius of gyration for a set of coordinates
    :param coords: the set of n coordinates.
    :type coords: (n,3) numpy array
    :param masses: the n input masses. If None the center of gravity is computed.
    :type masses: n-numpy array
    :param root: if True, return the square root of the radius of gyration.
    :type root: bool
    :return: the radius of gyration
    :rtype: float
    '''
    
    if masses is None:
        masses = numpy.ones((coords.shape[0]),dtype=numpy.float64)
            
    com = center_of_mass(coords,masses)
        
    rog = numpy.sum(numpy.sum((coords-com)**2,axis=1)*masses)/numpy.sum(masses)
    
    if root:
        rog = numpy.sqrt(rog)
        
    return rog

