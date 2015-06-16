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

:author: Eric C. Pellegrini
'''

import collections

from MDANSE import ELEMENTS
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

    type = 'dos'
    
    label = "Density Of States"

    category = ('Dynamics',)
    
    ancestor = "mmtk_trajectory"

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['instrument_resolution'] = ('instrument_resolution',{'dependencies':{'trajectory':'trajectory',
                                                                                       'frames' : 'frames'}})
    settings['interpolation_order'] = ('interpolation_order', {'label':"velocities",
                                                                    'dependencies':{'trajectory':'trajectory'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory',
                                                                         'grouping_level':'grouping_level'}})
    settings['grouping_level'] = ('grouping_level',{})
    settings['atom_transmutation'] = ('atom_transmutation',{'dependencies':{'trajectory':'trajectory',
                                                                                 'atom_selection':'atom_selection'}})        
    settings['weights'] = ('weights',{})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['atom_selection']['n_groups']

        instrResolution = self.configuration["instrument_resolution"]        
                
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        self._outputData.add("time_window","line", instrResolution["time_window"], axis="time", units="au") 

        self._outputData.add("frequency","line", instrResolution["frequencies"], units='THz')
        self._outputData.add("frequency_window","line", instrResolution["frequency_window"], axis="frequency", units="au") 
            
        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("vacf_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2") 
            self._outputData.add("dos_%s" % element,"line", (instrResolution['n_frequencies'],), axis="frequency", units="nm2/ps") 
        self._outputData.add("vacf_total","line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2")         
        self._outputData.add("dos_total","line", (instrResolution['n_frequencies'],), axis="frequency", units="nm2/ps")        
        
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
        indexes = self.configuration['atom_selection']["groups"][index]    
                        
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       variable=self.configuration['interpolation_order']["variable"])

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
        element = self.configuration['atom_selection']['elements'][index][0]
        
        self._outputData["vacf_%s" % element] += x
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["vacf_%s" % element][:] /= number
            self._outputData["dos_%s" % element][:] = get_spectrum(self._outputData["vacf_%s" % element],
                                                                   self.configuration["instrument_resolution"]["time_window"],
                                                                   self.configuration["instrument_resolution"]["time_step"])

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
        
        vacfTotal = weight(props,
                           self._outputData,
                           self.configuration['atom_selection']['n_atoms_per_element'],
                           1,
                           "vacf_%s")
        self._outputData["vacf_total"][:] = vacfTotal
        
        dosTotal = weight(props,
                          self._outputData,
                          self.configuration['atom_selection']['n_atoms_per_element'],
                          1,
                          "dos_%s")
        self._outputData["dos_total"][:] = dosTotal        
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
