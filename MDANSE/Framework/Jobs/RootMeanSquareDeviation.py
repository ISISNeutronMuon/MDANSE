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

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class RootMeanSquareDeviation(IJob):
    """
    The Root Mean-Square Deviation (RMSD) is one of the most popular measures of structural similarity. 
    It is a numerical measure of the difference between two structures. Typically, the RMSD is used to 
    quantify the structural evolution of the system during the simulation. 
    It can provide essential information about the structure, if it reached equilibrium or conversely 
    if major structural changes occurred during the simulation.
    """

    label = "Root Mean Square Deviation"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['reference_frame'] = ('integer', {'mini':0, 'default':0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']
        
        self._referenceIndex = self.configuration['reference_frame']['value']
        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
                                    
        # Will store the mean square deviation
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("rmsd_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="nm")
                
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.              
        """
        
        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]
        
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       weights=masses)

        # Compute the squared sum of the difference between all the coordinate of atoms i and the reference ones 
        squaredDiff = numpy.sum((series-series[self._referenceIndex,:])**2,axis=1)
                
        return index, squaredDiff
                        
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     
                
        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["rmsd_%s" % element] += x
        
    def finalize(self):
        """
        Finalize the job.
        """
                
        # The RMSDs per element are averaged.
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["rmsd_%s" % element] /= number

        weights = self.configuration["weights"].get_weights()
        rmsdTotal = weight(weights,self._outputData,nAtomsPerElement,1,"rmsd_%s")
        rmsdTotal = numpy.sqrt(rmsdTotal)
        self._outputData.add("rmsd_total","line", rmsdTotal, axis="time", units="nm") 
            
        for element, number in nAtomsPerElement.items():
            self._outputData["rmsd_%s" % element]  = numpy.sqrt(self._outputData["rmsd_%s" % element])
      
        # Write the output variables.
         
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
REGISTRY['rmsd'] = RootMeanSquareDeviation
                    