# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DensityOfStates.py
# @brief     Implements module/class/test DensityOfStates
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, differentiate, get_spectrum
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class DensityOfStates(IJob):
    """
    The Density Of States describes the number of vibrations per unit frequency. 
	It is determined as the power spectrum (Fourier transform) of the Velocity AutoCorrelation Function (VACF).
	The partial Density of States corresponds to selected sets of atoms or molecules.
	"""
    
    label = "Density Of States"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{'dependencies':{'trajectory':'trajectory','frames' : 'frames'}})
    settings['interpolation_order'] = ('interpolation_order', {'label':"velocities",'dependencies':{'trajectory':'trajectory'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation',{'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})        
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']

        instrResolution = self.configuration["instrument_resolution"]        
                
        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
        self._outputData.add("time_window","line", instrResolution["time_window"], axis="time", units="au") 

        self._outputData.add("omega","line", instrResolution["omega"], units='rad/ps')
        self._outputData.add("omega_window","line", instrResolution["omega_window"], axis="omega", units="au") 
            
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("vacf_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2") 
            self._outputData.add("dos_%s" % element,"line", (instrResolution['n_omegas'],), axis="omega", units="nm2/ps") 
        self._outputData.add("vacf_total","line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2")         
        self._outputData.add("dos_total","line", (instrResolution['n_omegas'],), axis="omega", units="nm2/ps")        
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicDOS (numpy.array): The calculated density of state for atom of index=index
            #. atomicVACF (numpy.array): The calculated velocity auto-correlation function for atom of index=index
        """

        # get atom index
        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]
                        
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       variable=self.configuration['interpolation_order']["variable"],
                                       weights=masses)

        val = self.configuration["interpolation_order"]["value"]
        
        if val != "no interpolation":     
            for axis in range(3):
                series[:,axis] = differentiate(series[:,axis], order=val, dt=self.configuration['frames']['time_step'])

        if self.configuration["projection"]["projector"] is not None:
            series = self.configuration['projection']["projector"](series)
            
        atomicVACF = correlation(series,axis=0,average=1)

        return index, atomicVACF

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """   

        # The symbol of the atom.
        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["vacf_%s" % element] += x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()        
        for element, number in nAtomsPerElement.items():
            self._outputData["vacf_%s" % element][:] /= number
            self._outputData["dos_%s" % element][:] = get_spectrum(self._outputData["vacf_%s" % element],
                                                                   self.configuration["instrument_resolution"]["time_window"],
                                                                   self.configuration["instrument_resolution"]["time_step"])

        weights = self.configuration["weights"].get_weights()
        vacfTotal = weight(weights,self._outputData,nAtomsPerElement,1,"vacf_%s")
        self._outputData["vacf_total"][:] = vacfTotal
        
        dosTotal = weight(weights,self._outputData,nAtomsPerElement,1,"dos_%s")
        self._outputData["dos_total"][:] = dosTotal        
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     

REGISTRY['dos'] = DensityOfStates
