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
Created on May 21, 2015

@author: Eric C. Pellegrini
'''

import collections

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, differentiate, normalize
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class VelocityAutoCorrelationFunction(IJob):
    """
    The Velocity AutoCorrelation Function (VACF) is a property describing
    the dynamics of a molecular system. It reveals the underlying nature of the forces acting
    on the system by computing the cartesian density of states for a set of atoms.

    In a molecular system that would be made of non interacting particles, the velocities would
    be constant at any time triggering the VACF to be a constant value. Now, if we think about a
    system with small interactions such as in a gas-phase, the magnitude and direction of the velocity
    of a particle will change gradually over time due to its collision with the other particles of the
    molecular system. In such a system, the VACF will be represented by a decaying exponential.
    
    In the case of solid phase, the interaction are much stronger and, as a results, the atoms
    are bound to a given position from which they will move backwards and forwards oscillating
    between positive and negative values of their velocity. The oscillations will not be of equal
    magnitude however, but will decay in time, because there are still perturbative forces acting on
    the atoms to disrupt the perfection of their oscillatory motion. So, in that case the VACF will
    look like a damped harmonic motion.
    
    Finally, in the case of liquid phase, the atoms have more freedom than in solid phase and
    because of the diffusion process, the oscillatory motion seen in solid phase will be cancelled quite
    rapidly depending on the density of the system. So, the VACF will just have one very damped
    oscillation before decaying to zero. This decaying time can be considered as the average time
    for a collision between two atoms to occur before they diffuse away.
    """

    type = 'vacf'
    
    label = "Velocity AutoCorrelation Function"

    category = ('Dynamics',)
    
    ancestor = "mmtk_trajectory"

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['interpolation_order'] = ('interpolation_order', {'label':"velocities",
                                                                    'dependencies':{'trajectory':'trajectory'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['normalize'] = ('boolean', {'default':False})
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
                        
        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
            
        # Will store the mean square displacement evolution.
        for element in self.configuration['atom_selection']['contents'].keys():
            self._outputData.add("vacf_%s" % element,"line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2") 

        self._outputData.add("vacf_total","line", (self.configuration['frames']['number'],), axis="time", units="nm2/ps2")         
                
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

        series = self.configuration['projection']["projector"](series)
                        
        atomicVACF = correlation(series,axis=0,reduce=1)
        
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

        # The MSDs per element are averaged.
        for element, number in self.configuration['atom_selection']['n_atoms_per_element'].items():
            self._outputData["vacf_%s" % element] /= number

        if self.configuration['normalize']["value"]:
            for element in self.configuration['atom_selection']['n_atoms_per_element'].keys():
                self._outputData["vacf_%s" % element] = normalize(self._outputData["vacf_%s" % element], axis=0)
                    
        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])
                    
        vacfTotal = weight(props,
                           self._outputData,
                           self.configuration['atom_selection']['n_atoms_per_element'],
                           1,
                           "vacf_%s")
        self._outputData["vacf_total"][:] = vacfTotal
                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     
  
        
    