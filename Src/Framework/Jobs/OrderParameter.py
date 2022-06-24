# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/OrderParameter.py
# @brief     Implements module/class/test OrderParameter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os

import numpy

from Scientific.Geometry import Vector
from Scientific.Geometry.Transformation import angleFromSineAndCosine, Rotation 

from MDANSE import REGISTRY
from MDANSE.Mathematics.Signal import correlation
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class OrderParameter(IJob):
    """
    The combination of NMR and MD simulation data is very powerful in the study of conformational dynamics of proteins. NMR relaxation 
    spectroscopy is a unique approach for a site-specific investigation of both global tumbling and internal motions of proteins. 
    The molecular motions modulate the magnetic interactions  between the nuclear spins and lead for each nuclear spin to a relaxation 
    behaviour which reflects its environment. 
	
	The relationship between microscopic motions and measured spin relaxation rates is given by Redfield's theory. The relaxation 
	measurements probe the relaxation dynamics of a selected nuclear spin at only a few frequencies. Moreover, only a limited number 
	of independent observables are accessible. Hence, to relate relaxation data to protein dynamics,  a dynamical model for molecular 
	motions or a functional form, depending on a limited number of adjustable parameters, are required. 
    
    The generalized order parameter, indicates the degree of spatial restriction of the internal motions of a bond vector, while the 
    characteristic time is an effective correlation time, setting the time scale of the internal relaxation processes. The resulting 
    values range from 0 (completely disordered) to 1 (fully ordered). 
    
    **Calculation:** \n
    angle at time T is calculated as the following: \n   
    .. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
    .. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )
    
    **Output:** \n      
    #. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`
    #. angular_correlation_legendre_2nd: :math:`<\\frac{1}{2}(3cos(\phi(T))^{2}-1)>`
    
    **Acknowledgement**\n
    AOUN Bachir, PELLEGRINI Eric
    """
        
    label = "Order parameter"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory', {'default':os.path.join('..','..','..','Data','Trajectories', 'MMTK', 'protein_in_periodic_universe.nc')})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['axis_selection'] = ('atoms_list', {'dependencies':{'trajectory':'trajectory'},
                                                 'nAtoms':2,
                                                 'default':('C284H438N84O79S7',('C','C_beta'))})
    settings['reference_direction'] = ('vector', {'default':[0,0,1], 'notNull':True, 'normalize':True})
    settings['per_axis'] = ('boolean', {'label':"output contribution per axis", 'default':False})
    settings['output_files'] = ('output_files', {'formats':["hdf","netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self._nFrames = self.configuration['frames']['number']
        self._nAxis = self.configuration['axis_selection']['n_values']
        
        self.numberOfSteps = self._nAxis

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')

        self._outputData.add("axis_index","line", numpy.arange(self.configuration['axis_selection']['n_values']), units='au')
                        
        self._zAxis = Vector([0,0,1])
        refAxis = self.configuration['reference_direction']['value']
        axis = self._zAxis.cross(refAxis)

        theta = angleFromSineAndCosine(axis.length(),self._zAxis*refAxis)

        try:
            self._rotation = Rotation(axis,theta).tensor.array
        except ZeroDivisionError:
            self._doRotation = False
        else:
            self._doRotation = True

        self._outputData.add('p1',"line", (self._nFrames,), axis='time', units="au") 
        self._outputData.add('p2',"line", (self._nFrames,), axis='time', units="au") 
        self._outputData.add('s2',"line", (self._nAxis,), axis='time', units="au") 
            
        if self.configuration['per_axis']['value']:
            self._outputData.add('p1_per_axis',"surface", (self._nAxis,self._nFrames), axis='axis_index|time', units="au") 
            self._outputData.add('p2_per_axis',"surface", (self._nAxis,self._nFrames), axis='axis_index|time', units="au") 

    def run_step(self, index):
        """
        Runs a single step of the job.
 
        :param index: the index of the step.
        :type index: int
        :return: a 2-tuple whose 1st element is the index of the step and 2nd element resp. p1, p2, s2 vectors.
        :rtype: 2-tuple
        """

        e1, e2 = self.configuration['axis_selection']['atoms'][index]
        
        e1 = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                   e1,
                                   first=self.configuration['frames']['first'],
                                   last=self.configuration['frames']['last']+1,
                                   step=self.configuration['frames']['step'])

        e2 = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                   e2,
                                   first=self.configuration['frames']['first'],
                                   last=self.configuration['frames']['last']+1,
                                   step=self.configuration['frames']['step'])

        diff = e2 - e1

        modulus = numpy.sqrt(numpy.sum(diff**2,1))
        
        diff /= modulus[:,numpy.newaxis]
        
        # shape (3,n)
        tDiff = diff.T
        
        if self._doRotation:
            diff = numpy.dot(self._rotation,tDiff)
                
        costheta = numpy.dot(self._zAxis.array,tDiff)
        sintheta = numpy.sqrt(numpy.sum(numpy.cross(self._zAxis,tDiff,axisb=0)**2,1))
        
        cosphi = tDiff[0,:]/sintheta
        sinphi = tDiff[1,:]/sintheta

        tr2         = 3.0*costheta**2 - 1.
        cos2phi     = 2.0*cosphi**2-1.
        sin2phi     = 2.0*sinphi*cosphi
        cossintheta = costheta*sintheta
        sintheta_sq = sintheta**2
                
        # 1st order legendre polynomia
        p1 = correlation(costheta)

        # Formula for the 2nd legendre polynomia applied to spherical coordinates
        p2 = (0.25*correlation(tr2) + 
              3.00*correlation(cosphi*cossintheta) + 
              3.00*correlation(sinphi*cossintheta) + 
              0.75*correlation(cos2phi*sintheta_sq) + 
              0.75*correlation(sin2phi*sintheta_sq))

        # s2 calculation (s2 = lim (t->+inf) p2)
        s2 = (0.75 * (numpy.sum(cos2phi*sintheta_sq)**2 + numpy.sum(sin2phi*sintheta_sq)**2) + \
              3.00 * (numpy.sum(cosphi*cossintheta)**2 + numpy.sum(sinphi*cossintheta)**2) +
              0.25 *  numpy.sum(tr2)**2) / self._nFrames**2
        
        return index, (p1, p2, s2)

    def combine(self, index, x):
        """
        Combines/synchronizes the output of `run_step` method.
        
        :param index: the index of the step.
        :type index: int
        :param x: the output of `run_step` method.
        :type x: any python object
        """     
        
        p1, p2, s2 = x
        
        self._outputData['p1'] += p1
        self._outputData['p2'] += p2
        self._outputData['s2'][index] = s2
        
        if self.configuration['per_axis']['value']:
            self._outputData['p1_per_axis'][index,:] = p1
            self._outputData['p2_per_axis'][index,:] = p2
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 
             
        self._outputData['p1'] /= self._nAxis
        self._outputData['p2'] /= self._nAxis
                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     

REGISTRY['op'] = OrderParameter
