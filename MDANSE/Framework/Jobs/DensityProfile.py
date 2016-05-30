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
Created on Apr 10, 2015

:author: Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight

class DensityProfileError(Error):
    pass

class DensityProfile(IJob):
    """
    The Density Profile analysis shows the weighted atomic density heterogeneity in the directions of the simulation box axes.
    For a lipid membrane, the density variation in the direction perpendicular to the membrane is probed in reflectometry measurements.	
    The Density Profile Analysis can show segregation or cluster order formation, for example during the formation of micelles. 
    """
    type = 'dp'

    label = "Density Profile"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation',{'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['axis'] = ('single_choice', {'choices':['a','b','c'], 'default':'c'})
    settings['dr'] = ('float', {'default':0.01, 'mini':1.0e-9})
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
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

        self._indexesPerElement = self.configuration['atom_selection'].get_indexes()

        for element in self._indexesPerElement.keys():
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
        
        for k,v in self._indexesPerElement.iteritems():
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
 
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()        
        for element in nAtomsPerElement.keys():
            self._outputData["dp_%s" % element] += self.numberOfSteps

        dpTotal = weight(self.configuration["weights"].get_weights(),self._outputData,nAtomsPerElement,1,"dp_%s")
            
        self._outputData.add("dp_total","line", dpTotal, axis="r", units="au") 
        
        self._extent /= self.numberOfSteps
                
        rValues = self._extent*numpy.linspace(0,1,self._nBins+1)
        self._outputData["r"][:] = (rValues[1:]+rValues[:-1])/2

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
         
        self.configuration['trajectory']['instance'].close()