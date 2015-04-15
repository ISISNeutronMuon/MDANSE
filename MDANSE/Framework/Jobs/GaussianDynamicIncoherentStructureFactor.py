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
Created on Apr 10, 2015

@author: pellegrini
'''

import collections

import numpy

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class GaussianDynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor for a set of atoms with the gaussian approximation.
    """
    
    type = 'gdisf'
    
    label = "Gaussian Dynamic Incoherent Structure Factor"

    category = ('Scattering',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies' : {'trajectory':'trajectory'}})
    settings['q_shells'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['instrument_resolution'] = ('instrument_resolution', {'dependencies':{'trajectory':'trajectory',
                                                                                        'frames' : 'frames'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory',
                                                                          'grouping_level':'grouping_level'}})
    settings['grouping_level'] = ('grouping_level',{})
    settings['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_incoherent'})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['n_groups']

        self._nQShells = self.configuration["q_shells"]["number"]
        
        self._nFrames = self.configuration['frames']['number']
        
        self._instrResolution = self.configuration["instrument_resolution"]
        
        self._nFrequencies = self._instrResolution['n_frequencies']
        
        self._kSquare = self.configuration["q_shells"]["value"]**2
        
        self._outputData.add("q","line",self.configuration["q_shells"]["value"], units="inv_nm") 

        self._outputData.add("q2","line",self._kSquare,units="inv_nm**2") 

        self._outputData.add("times","line",self.configuration['frames']['time'], units='ps')
        self._outputData.add("time_window","line",self._instrResolution["time_window"], axis="times", units="au") 

        self._outputData.add("frequency","line",self.configuration["instrument_resolution"]["frequencies"], units='THz')
        self._outputData.add("frequency_window","line",self._instrResolution["frequency_window"], axis="frequency", units="au") 

        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("f(q,t)_%s" % element,"surface", (self._nQShells,self._nFrames),axis="q|times", units="au")                                                 
            self._outputData.add("s(q,f)_%s" % element,"surface", (self._nQShells,self._nFrequencies), axis="q|frequency", units="nm2/ps") 

        self._outputData.add("f(q,t)_total","surface",(self._nQShells,self._nFrames), axis="q|times", units="au")                                                 
        self._outputData.add("s(q,f)_total","surface",(self._nQShells,self._nFrequencies), axis="q|frequency", units="nm2/ps") 
        
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
        indexes = self.configuration['atom_selection']["groups"][index]                                                                          
                
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'])
        
        series = self.configuration['projection']["projector"](series)

        atomicSF = numpy.zeros((self._nQShells,self._nFrames), dtype=numpy.float64)
                
        msd  = mean_square_displacement(series)

        for i, q2 in enumerate(self._kSquare):
            
            gaussian = numpy.exp(-msd*q2/6.0)

            atomicSF[i,:] += gaussian

        return index, atomicSF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration['atom_selection']['elements'][index][0]
        
        self._outputData["f(q,t)_%s" % element] += x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["f(q,t)_%s" % element][:] /= number
            self._outputData["s(q,f)_%s" % element][:] = get_spectrum(self._outputData["f(q,t)_%s" % element],
                                                                      self.configuration["instrument_resolution"]["time_window"],
                                                                      self.configuration["instrument_resolution"]["time_step"],
                                                                      axis=1)

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
        
        self._outputData["f(q,t)_total"][:] = weight(props,self._outputData,self.configuration['atom_selection']['n_atoms_per_element'],1,"f(q,t)_%s")
        
        self._outputData["s(q,f)_total"][:] = weight(props,self._outputData,self.configuration['atom_selection']['n_atoms_per_element'],1,"s(q,f)_%s")
    
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()