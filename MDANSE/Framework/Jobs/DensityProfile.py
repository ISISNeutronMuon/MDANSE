#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
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
Created on Apr 10, 2015

@author: pellegrini
'''

import collections

import numpy

from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight

class DensityProfileError(Error):
    pass

class DensityProfile(IJob):
    """
    The Density Profile analysis can be used to characterize the density heterogeneity in order to study 
    atoms segregation and cluster order formation in long chained molecules systems such as polymers, lipids, etc. 
    """
    type = 'dp'

    label = "Density Profile"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"
    
    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    configurators['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    configurators['transmutated_atoms'] = ('atom_transmutation',{'dependencies':{'trajectory':'trajectory',
                                                                                 'atom_selection':'atom_selection'}})
    configurators['axis'] = ('single_choice', {'choices':['a','b','c'], 'default':'c'})
    configurators['dr'] = ('float', {'default':0.01, 'mini':1.0e-9})
    configurators['weights'] = ('weights',{})
    configurators['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    configurators['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration['frames']['number']
                
        self.dr = self.configuration["dr"]["value"]
                
        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise DensityProfileError('Cannot start %s analysis on non-periodic system' % self.label)
        
        axis = self.configuration["axis"]["index"]
        dr = self.configuration["dr"]["value"]
        self._nBins = int(self.configuration['trajectory']['instance'].universe.basisVectors()[axis].length()/dr)+1
                                
        self._outputData.add('r',"line", (self._nBins,), units="nm") 

        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("dp_%s" % element,"line", (self._nBins,), axis="r", units="au") 

        self._extent = 0.0
                                
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @param trajectory: the trajectory.
        @type trajectory: MMTK trajectory.                
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
                  
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
                        
        conf = self.configuration['trajectory']['instance'].universe.configuration()

        conf.convertToBoxCoordinates()

        axis = self.configuration["axis"]["index"]
        extent = self.configuration['trajectory']['instance'].universe.basisVectors()[axis].length()
        
        dpPerFrame = {}
        
        for k,v in self.configuration['atom_selection']["contents"].iteritems():
            h = numpy.histogram(conf.array[v,self.configuration["axis"]["index"]],bins=self._nBins, range=[-0.5,0.5])
            dpPerFrame[k] = h[0]
            
        return index, (extent,dpPerFrame)
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """
        
        self._extent += x[0]
        
        for element, hist in x[1].items():
            self._outputData["dp_%s" % element] += hist
                        
    def finalize(self):
        """
        Finalize the job.
        """
 
        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData["dp_%s" % element] += self.numberOfSteps

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])

        dpTotal = weight(props,
                         self._outputData,
                         self.configuration['atom_selection']['n_atoms_per_element'],
                         1,
                         "dp_%s")
            
        self._outputData.add("dp_total","line", dpTotal, axis="times", units="au") 
        
        self._extent /= self.numberOfSteps
                
        rValues = self._extent*numpy.linspace(0,1,self._nBins+1)
        self._outputData["r"][:] = (rValues[1:]+rValues[:-1])/2

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
         
        self.configuration['trajectory']['instance'].close()