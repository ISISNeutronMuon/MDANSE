# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DynamicIncoherentStructureFactor.py
# @brief     Implements module/class/test DynamicIncoherentStructureFactor
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class DynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms.
	It can be compared to experimental data e.g. the quasielastic scattering due to diffusion processes.
    """
    
    label = "Dynamic Incoherent Structure Factor"

    category = ('Analysis','Scattering',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]
    
    settings = collections.OrderedDict()
    settings['trajectory']=('mmtk_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{"dependencies":{'trajectory':'trajectory', 'frames' : 'frames'}})
    settings['q_vectors'] = ('q_vectors',{"dependencies":{'trajectory':'trajectory'}})
    settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
    settings['projection']=('projection', {"label":"project coordinates"})
    settings['weights'] = ('weights', {'default':'b_incoherent2',"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['output_files']=('output_files', {"formats":["netcdf","ascii"]})
    settings['running_mode']=('running_mode',{})
                    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["q_vectors"]["n_shells"]

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nOmegas = self._instrResolution['n_omegas']

        self._outputData.add("q","line", self.configuration["q_vectors"]["shells"], units="1/nm") 

        self._outputData.add("time","line", self.configuration['frames']['duration'], units='ps')
        self._outputData.add("time_window","line", self._instrResolution["time_window"], axis="time", units="au") 

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
            #. atomicSF (numpy.array): The atomic structure factor
        """
        
        shell = self.configuration["q_vectors"]["shells"][index]
        
        if not shell in self.configuration["q_vectors"]["value"]:
            return index, None
            
        else:

            qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]


            disf_per_q_shell = {}
            for element in self.configuration['atom_selection']['unique_names']:
                disf_per_q_shell[element] = numpy.zeros((self._nFrames,), dtype = numpy.float)

            for i,atom_indexes in enumerate(self.configuration['atom_selection']["indexes"]):

                masses = self.configuration['atom_selection']["masses"][i]

                element = self.configuration['atom_selection']["names"][i]
                        
                series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                               atom_indexes,
                                               first=self.configuration['frames']['first'],
                                               last=self.configuration['frames']['last']+1,
                                               step=self.configuration['frames']['step'],
                                               weights=[masses])
                
                series = self.configuration['projection']["projector"](series)
                                                                                    
                rho = numpy.exp(1j*numpy.dot(series, qVectors))
                res = correlation(rho, axis=0, average=1)
                    
                disf_per_q_shell[element] += res
        
        return index, disf_per_q_shell
    
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        if x is not None: 
            for k,v in x.items():
                self._outputData["f(q,t)_%s" % k][index,:] += v
                        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for element, number in nAtomsPerElement.items():
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
