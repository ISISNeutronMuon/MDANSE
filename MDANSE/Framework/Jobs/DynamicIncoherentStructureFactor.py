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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, get_spectrum
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class DynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms.
	It can be compared to experimental data e.g. the quasielastic scattering due to diffusion processes.
    """

    type = 'disf'
    
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

        self.numberOfSteps = self.configuration['atom_selection']['selection_length']

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nOmegas = self._instrResolution['n_omegas']

        self._outputData.add("q","line", self.configuration["q_vectors"]["shells"], units="inv_nm") 

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
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

        atomicSF = numpy.zeros((self._nQShells,self._nFrames), dtype=numpy.float64)

        for i,q in enumerate(self.configuration["q_vectors"]["shells"]):
                        
            if not q in self.configuration["q_vectors"]["value"]:
                continue
            
            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]
                        
            rho = numpy.exp(1j*numpy.dot(series, qVectors))
            res = correlation(rho, axis=0, average=1)
            
            atomicSF[i,:] += res
        
        return index, atomicSF
    
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
                
        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["f(q,t)_%s" % element] += x
            
    
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