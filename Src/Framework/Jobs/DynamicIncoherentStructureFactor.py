# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DynamicIncoherentStructureFactor.py
# @brief     Implements module/class/test DynamicIncoherentStructureFactor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

class DynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms.
	It can be compared to experimental data e.g. the quasielastic scattering due to diffusion processes.
    """
    
    label = "Dynamic Incoherent Structure Factor"

    category = ('Analysis','Scattering',)
    
    ancestor = ['hdf_trajectory','molecular_viewer']
    
    settings = collections.OrderedDict()
    settings['trajectory']=('hdf_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{"dependencies":{'trajectory':'trajectory', 'frames' : 'frames'}})
    settings['q_vectors'] = ('q_vectors',{"dependencies":{'trajectory':'trajectory'}})
    settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
    settings['projection']=('projection', {"label":"project coordinates"})
    settings['weights'] = ('weights', {'default':'b_incoherent2',"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['output_files']=('output_files', {'formats':['hdf','netcdf','ascii']})
    settings['running_mode']=('running_mode',{})
                    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._atoms = sorted_atoms(self.configuration["trajectory"]["instance"].chemical_system.atom_list())

        self._nOmegas = self._instrResolution['n_omegas']

        self._outputData.add("q","line", self.configuration["q_vectors"]["shells"], units="1/nm") 

        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
        self._outputData.add("time_window","line", self._instrResolution["time_window"], units="au") 

        self._outputData.add("omega","line", self._instrResolution["omega"], units='rad/ps')
        self._outputData.add("omega_window","line", self._instrResolution["omega_window"], axis="omega", units="au") 
                        
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("f(q,t)_%s" % element,"surface", (self._nQShells,self._nFrames)     , axis="q|time", units="au")                                                 
            self._outputData.add("s(q,f)_%s" % element,"surface", (self._nQShells,self._nOmegas), axis="q|omega", units="nm2/ps") 

        self._outputData.add("f(q,t)_total","surface", (self._nQShells,self._nFrames)     , axis="q|time", units="au")                                                 
        self._outputData.add("s(q,f)_total","surface", (self._nQShells,self._nOmegas), axis="q|omega", units="nm2/ps")
    
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicSF (np.array): The atomic structure factor
        """

        indexes = self.configuration['atom_selection']["indexes"][index]

        if len(indexes) == 1:
            series = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
                indexes[0],
                first=self.configuration['frames']['first'],
                last=self.configuration['frames']['last']+1,
                step=self.configuration['frames']['step'],
            )

        else:
            selected_atoms = [self._atoms[idx] for idx in indexes]
            series = self.configuration["trajectory"]["instance"].read_com_trajectory(
                selected_atoms,
                first=self.configuration['frames']['first'],
                last=self.configuration['frames']['last']+1,
                step=self.configuration['frames']['step'],
            )
        
        series = self.configuration['projection']["projector"](series)

        disf_per_q_shell = collections.OrderedDict()
        for q in self.configuration["q_vectors"]["shells"]:
            disf_per_q_shell[q] = np.zeros((self._nFrames,), dtype=np.float)

        for q in self.configuration["q_vectors"]["shells"]:
            
            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]

            rho = np.exp(1j*np.dot(series, qVectors))
            res = correlation(rho, axis=0, average=1)

            disf_per_q_shell[q] += res

        return index, disf_per_q_shell
        
    def combine(self, index, disf_per_q_shell):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        element = self.configuration['atom_selection']["names"][index]
        for i, v in enumerate(disf_per_q_shell.values()):
            self._outputData["f(q,t)_{}".format(element)][i,:] += v
                        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["f(q,t)_%s" % element][:] /= number
            self._outputData["s(q,f)_%s" % element][:] = get_spectrum(self._outputData["f(q,t)_%s" % element],
                                                                      self.configuration["instrument_resolution"]["time_window"],
                                                                      self.configuration["instrument_resolution"]["time_step"],
                                                                      axis=1)

        weights = self.configuration["weights"].get_weights()
                
        self._outputData["f(q,t)_total"][:] = weight(weights,self._outputData,nAtomsPerElement,1,"f(q,t)_%s")
        
        self._outputData["s(q,f)_total"][:] = weight(weights,self._outputData,nAtomsPerElement,1,"s(q,f)_%s")
    
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['disf'] = DynamicIncoherentStructureFactor
