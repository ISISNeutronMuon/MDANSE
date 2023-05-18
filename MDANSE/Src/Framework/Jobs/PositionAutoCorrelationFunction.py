# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/PositionAutoCorrelationFunction.py
# @brief     Implements module/class/test PositionAutoCorrelationFunction
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
from MDANSE.Mathematics.Signal import correlation, normalize
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

class PositionAutoCorrelationFunction(IJob):
    """
    Like the velocity autocorrelation function, but using positions instead of velocities.
    """
        
    label = "Position AutoCorrelation Function"

    category = ('Analysis','Dynamics',)
    
    ancestor = ['hdf_trajectory','molecular_viewer']
    
    settings = collections.OrderedDict()      
    settings['trajectory'] = ('hdf_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['normalize'] = ('boolean', {'default':False})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})        
    settings['weights']=('weights',{'dependencies':{'atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':['hdf','netcdf','ascii']})
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
            
        self._atoms = sorted_atoms(self.configuration["trajectory"]["instance"].chemical_system.atom_list())

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicPACF (np.array): The calculated position auto-correlation function for atom index
        """
        
        # get atom index
        indexes = self.configuration['atom_selection']["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]
                        
        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration['frames']['first'],
            last=self.configuration['frames']['last']+1,
            step=self.configuration['frames']['step'])

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
        self.configuration['atom_selection']['n_atoms_per_element'] = nAtomsPerElement

        for element, number in list(nAtomsPerElement.items()):
            self._outputData["pacf_%s" % element] /= number
                
        if self.configuration['normalize']["value"]:
            for element in list(nAtomsPerElement.keys()):
                if self._outputData["pacf_%s" % element][0] == 0:
                    raise ValueError("The normalization factor is equal to zero !!!") 
                else:
                    self._outputData["pacf_%s" % element] = normalize(self._outputData["pacf_%s" % element], axis=0)

        weights = self.configuration["weights"].get_weights()
        pacfTotal = weight(weights,self._outputData,nAtomsPerElement,1,"pacf_%s")
        
        self._outputData.add("pacf_total","line", pacfTotal, axis="time", units="nm2") 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
REGISTRY['pacf'] = PositionAutoCorrelationFunction
