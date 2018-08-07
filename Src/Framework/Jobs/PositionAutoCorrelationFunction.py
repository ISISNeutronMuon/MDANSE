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

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class PositionAutoCorrelationFunction(IJob):
    """
    Like the velocity autocorrelation function, but using positions instead of velocities.
    """
        
    label = "Position AutoCorrelation Function"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()      
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['normalize'] = ('boolean', {'default':False})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})        
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['atom_selection']['selection_length']
                        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
                    
        # Will store the mean square displacement evolution.
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("pacf_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="nm2")
            
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicPACF (numpy.array): The calculated position auto-correlation function for atom index
        """
        
        # get atom index
        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]

        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       weights=masses)    

        series = self.configuration['projection']["projector"](series)
        
        atomicPACF = correlation(series,axis=0,average=1)
        
        return index, atomicPACF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     
        
        # The symbol of the atom.
        element = self.configuration['atom_selection']["names"][index]

        # The MSD for element |symbol| is updated.
        self._outputData["pacf_%s" % element] += x        
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["pacf_%s" % element] /= number
                
        if self.configuration['normalize']["value"]:
            for element in self.configuration['atom_selection']['n_atoms_per_element'].keys():
                pacf = self._outputData["pacf_%s" % element]      
                if pacf[0] == 0:
                    raise ValueError("The normalization factor is equal to zero !!!") 
                else:
                    pacf /= pacf[0]

        weights = self.configuration["weights"].get_weights()
        pacfTotal = weight(weights,self._outputData,nAtomsPerElement,1,"pacf_%s")
        
        self._outputData.add("pacf_total","line", pacfTotal, axis="time", units="nm2") 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
REGISTRY['pacf'] = PositionAutoCorrelationFunction
