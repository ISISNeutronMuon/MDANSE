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

@author: Eric C. Pellegrini
'''

import collections

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class PositionAutoCorrelationFunction(IJob):
    """
    Like the velocity autocorrelation function, but using positions instead of velocities.
    """
    
    type = 'pacf'
    
    label = "Position AutoCorrelation Function"

    category = ('Dynamics',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()      
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['normalize'] = ('boolean', {'default':False})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory',
                                                                          'grouping_level':'grouping_level'}})
    settings['grouping_level'] = ('grouping_level',{})
    settings['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})        
    settings['weights'] = ('weights',{})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['atom_selection']['n_groups']
                        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
                    
        # Will store the mean square displacement evolution.
        for element in self.configuration['atom_selection']['contents'].keys():
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
        indexes = self.configuration['atom_selection']["groups"][index]                                                                          

        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'])    

        series = self.configuration['projection']["projector"](series)
        
        atomicPACF = correlation(series,axis=0,reduce=1)
        
        return index, atomicPACF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     
        
        # The symbol of the atom.
        element = self.configuration['atom_selection']['elements'][index][0]       

        # The MSD for element |symbol| is updated.
        self._outputData["pacf_%s" % element] += x        
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        # The MSDs per element are averaged.
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["pacf_%s" % element] /= number
                
        if self.configuration['normalize']["value"]:
            for element in self.configuration['atom_selection']['n_atoms_per_element'].keys():
                pacf = self._outputData["pacf_%s" % element]      
                if pacf[0] == 0:
                    raise ValueError("The normalization factor is equal to zero !!!") 
                else:
                    pacf /= pacf[0]

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
                    
        pacfTotal = weight(props,
                           self._outputData,
                           self.configuration['atom_selection']['n_atoms_per_element'],
                           1,
                           "pacf_%s")
        
        self._outputData.add("pacf_total","line", pacfTotal, axis="time", units="nm2") 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
        
                        
    