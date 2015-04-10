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
Created on Mar 30, 2015

@author: pellegrini
'''

import collections

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class MeanSquareDisplacement(IJob):
    """
    Molecules in liquids and gases do not stay in the same place, but move constantly. This
    process is called diffusion and it happens quite naturally in 
    liquids at equilibrium. 
    
    During this process, the motion of an individual molecule does not follow a simple path. 
    As it travels, the molecule undergoes some collisions with other molecules which prevent it 
    from following a straight line. If the path is examined in close detail, 
    it will be seen to be a good approximation to a random walk. 
    
    Mathematically, a random walk is a series of steps where each step is taken in a completely 
    random direction from the one before. This kind of path was famously analysed by Albert Einstein 
    in a study of Brownian motion. He showed that the MSD of a particle following a random walk 
    is proportional to the time elapsed. This relationship can be written as :
    
    .. math:: <r^{2}> = 6Dt + C 
    
    where <r^2> is the MSD and t is the time. D and C are constants. The constant D defines
    the so-called diffusion coefficient.
    """
    
    type = 'msd'
    
    label = "Mean Square Displacement"

    category = ('Dynamics',)
    
    ancestor = "mmtk_trajectory"
    
    configurators = collections.OrderedDict()
    configurators['trajectory']=('mmtk_trajectory',{})
    configurators['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    configurators['projection']=('projection', {"label":"project coordinates"})
    configurators['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory','grouping_level':'grouping_level'}})
    configurators['grouping_level']=('grouping_level',{})
    configurators['transmutated_atoms']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
    configurators['weights']=('weights',{})
    configurators['output_files']=('output_files', {"formats":["netcdf","ascii"]})
    configurators['running_mode']=('running_mode',{})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['n_groups']
                        
        # Will store the time.
        self._outputData.add("times", "line", self.configuration['frames']['time'], units='ps')
                        
        # Will store the mean square displacement evolution.
        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("msd_%s" % element, "line", (self.configuration['frames']['number'],), axis="times", units="nm2") 


    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicMSD (numpy.array): The calculated mean square displacement for atom index
        """
                
        # get atom index
        indexes = self.configuration['atom_selection']["groups"][index]
                        
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'])
         
        series = self.configuration['projection']["projector"](series)
 
        msd = mean_square_displacement(series)
        
        return index, msd
    
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     
                
        # The symbol of the atom.
        element = self.configuration['atom_selection']['elements'][index][0]
        
        self._outputData["msd_%s" % element] += x
            
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        # The MSDs per element are averaged.
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["msd_%s" % element] /= number

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
        
        msdTotal = weight(props,
                          self._outputData,
                          self.configuration['atom_selection']['n_atoms_per_element'],
                          1,
                          "msd_%s")
        
        self._outputData.add("msd_total", "line", msdTotal, axis="times", units="nm2") 
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     