# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/MeanSquareDisplacement.py
# @brief     Implements module/class/test MeanSquareDisplacement
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class MeanSquareDisplacement(IJob):
    """
    Molecules in liquids and gases do not stay in the same place, but move constantly. This
    process is called diffusion and it takes place in 
    liquids at equilibrium. 
    
    During this process, the motion of an individual molecule does not follow a simple path 
    since molecules undergo collisions. The path is to a good approximation to a random walk. 
    
    Mathematically, a random walk is a series of steps where each step is taken in a completely 
    random direction from the one before, as analyzed by Albert Einstein 
    in a study of Brownian motion. The MSD of a particle in this case 
    is proportional to the time elapsed:
    
    .. math:: <r^{2}> = 6Dt + C 
    
    where :math:`<r^{2}>` is the MSD and t is the time. D and C are constants. The constant D is
    the so-called diffusion coefficient.
	
	More generally the MSD reveals the distance or volume explored by atoms and molecules as a function of time.
	In crystals, the MSD quickly saturates at a constant value which corresponds to the vibrational amplitude.
	Diffusion in a volume will also have a limiting value of the MSD  which corresponds to the diameter of the volume
	and the saturation value is reached more slowly.
	The MSD can also reveal e.g. sub-diffusion regimes for the translational diffusion of lipids in membranes.
    """
        
    label = "Mean Square Displacement"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory']=('mmtk_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['projection']=('projection', {"label":"project coordinates"})
    settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files']=('output_files', {"formats":["hdf","netcdf","ascii","svg"]})
    settings['running_mode']=('running_mode',{})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']
                        
        # Will store the time.
        self._outputData.add("time", "line", self.configuration['frames']['duration'], units='ps')
                        
        # Will store the mean square displacement evolution.
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("msd_%s" % element, "line", (self.configuration['frames']['number'],), axis="time", units="nm2") 

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
        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]
                        
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       weights=masses)
         
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
        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["msd_%s" % element] += x
            
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        # The MSDs per element are averaged.
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["msd_%s" % element] /= number

        weights = self.configuration["weights"].get_weights()
        msdTotal = weight(weights,self._outputData,nAtomsPerElement,1,"msd_%s")
        
        self._outputData.add("msd_total", "line", msdTotal, axis="time", units="nm2") 
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['msd'] = MeanSquareDisplacement
