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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Analysis import mean_square_fluctuation
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class RootMeanSquareFluctuation(IJob):
    """
    The root mean square fluctuation (RMSF) for a set of atoms is similar to the square root
	of the mean square displacement (MSD), except that it is spatially resolved (by atom/residue/etc)
	rather than time resolved. It reveals the dynamical heterogeneity of the molecule over the course
	of a MD simulation.
    """

    type = 'rmsf'

    label = "Root Mean Square Fluctuation"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory',
                                                                          'grouping_level':'grouping_level'}})
    settings['grouping_level'] = ('grouping_level',{})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['atom_selection']['n_groups']
        
        # Will store the indexes.
        
        self._outputData.add('indexes',"line",self.configuration['atom_selection']['indexes'])
            
        # Will store the mean square fluctuation evolution.
        self._outputData.add('rmsf',"line",(self.configuration['atom_selection']['n_selected_atoms'],),'indexes')
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. rmsf (numpy.array): the calculated root mean square fluctuation for atom index
        """
        # read the particle trajectory  
        atomIndex = self.configuration['atom_selection']['groups'][index]   
        
        # read the particle trajectory                                              
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                               atomIndex,
                               first=self.configuration['frames']['first'],
                               last=self.configuration['frames']['last']+1,
                               step=self.configuration['frames']['step'])
        
        rmsf = mean_square_fluctuation(series,root=True)

        return index, rmsf
                    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        
        self._outputData['rmsf'][index] = x
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()         