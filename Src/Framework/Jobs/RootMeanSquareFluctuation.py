# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RootMeanSquareFluctuation.py
# @brief     Implements module/class/test RootMeanSquareFluctuation
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MDANSE import REGISTRY
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

    label = "Root Mean Square Fluctuation"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['atom_selection']['selection_length']
        
        # Will store the indexes.
        indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]        
        self._outputData.add('indexes',"line",indexes)
            
        # Will store the mean square fluctuation evolution.
        self._outputData.add('rmsf',"line",(self.configuration['atom_selection']['selection_length'],),axis='indexes',units='nm')
        
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
        indexes = self.configuration['atom_selection']["indexes"][index]
        
        # read the particle trajectory                                              
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
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
        
REGISTRY['rmsf'] = RootMeanSquareFluctuation
