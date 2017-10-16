#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#71 avenue des Martyrs
#38000 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

'''
Created on Jun 9, 2015

:author: Bachir Aoun and Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Mathematics.Signal import correlation

class DipoleAutoCorrelationFunction(IJob):
    """
    """
    
    label = "Dipole AutoCorrelation Function"
    
    category = ('Analysis','Infrared',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'},'default' : 'atom_index 0,1,2'})
    settings['atom_charges'] = ('partial_charges',{'dependencies':{'trajectory':'trajectory'},'default':{0:0.5,1:1.2,2:-0.2}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
                        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
        
        self._dipoleMoments = numpy.zeros((self.configuration['frames']['number'],3),dtype=numpy.float64)
            
        self._outputData.add("dacf","line", (self.configuration['frames']['number'],), axis="time")
        
        if not isinstance(self.configuration["atom_charges"]["charges"],dict):
            raise JobError(self,'Invalid type for partial charges. Must be a dictionary that maps atom index to to partial charge.')
            
        self._indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]
        for idx in self._indexes: 
            if not self.configuration["atom_charges"]["charges"].has_key(idx):
                raise JobError(self,'Partial charge not defined for atom: %d' % idx)                         
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. dipolarAC (numpy.array): The calculated dipolar auto-correlation function for atom of index=index
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]   

        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()

        dipoleMoment = numpy.zeros((3,),dtype=numpy.float64)
        for idx in self._indexes:
            temp = self.configuration["atom_charges"]["charges"][idx]*conf[idx]
            # Loop to sum temp because MMTK redefines __add__ operator, leading to a crash
            #dipoleMoment = dipoleMoment + self.configuration["atom_charges"]["charges"][idx]*conf[idx]
            for k in range(len(temp)):
                dipoleMoment[k] = dipoleMoment[k] + temp[k]
                
        return index, dipoleMoment

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """   

        self._dipoleMoments[index] = x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        
        self._outputData["dacf"][:] = correlation(self._dipoleMoments,axis=0,average=1)
                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
    
REGISTRY['dacf'] = DipoleAutoCorrelationFunction
