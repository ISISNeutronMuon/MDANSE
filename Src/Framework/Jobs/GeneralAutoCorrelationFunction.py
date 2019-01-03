import collections

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class GeneralAutoCorrelationFunction(IJob):
    """
    Computes the autocorrelation for any available trajectory variable.
    """
        
    label = "General AutoCorrelation Function"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})        
    settings['trajectory_variable'] = ('trajectory_variable', {'dependencies':{'trajectory':'trajectory'}})
    settings['normalize'] = ('boolean', {'default':False})
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
            self._outputData.add("gacf_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="au")

        self._outputData.add("gacf_total","line", (self.configuration['frames']['number'],), axis="time", units="au") 
  
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): the index of the step.
        :Returns:
            #. index (int): the index of the step. 
            #. atomicGACF (numpy.array): the calculated auto-correlation function for the index
        """

        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]

        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       weights=masses,
                                       variable=self.configuration["trajectory_variable"]["value"])
                
        atomicGACF = correlation(series,axis=0,average=1)
        
        return index, atomicGACF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """     

        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["gacf_%s" % element] += x        
        
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 
        
        # The MSDs per element are averaged.
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["gacf_%s" % element] /= number
                
        if self.configuration['normalize']["value"]:
            for element in self.configuration['atom_selection']['n_atoms_per_element'].keys():
                pacf = self._outputData["gacf_%s" % element]      
                if pacf[0] == 0:
                    raise ValueError("The normalization factor is equal to zero !!!") 
                else:
                    pacf /= pacf[0]

        weights = self.configuration["weights"].get_weights()
        gacfTotal = weight(weights,self._outputData,nAtomsPerElement,1,"gacf_%s")
        
        self._outputData["gacf_total"][:] = gacfTotal 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['gacf'] = GeneralAutoCorrelationFunction
