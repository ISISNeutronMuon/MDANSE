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
Created on May 21, 2015

:author: Eric C. Pellegrini
'''

import collections

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import correlation, differentiate, normalize
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class VelocityAutoCorrelationFunction(IJob):
    """
    The Velocity AutoCorrelation Function (VACF) is a property describing the dynamics of a molecular system. 
    It reveals the underlying nature of the forces acting on the system. Its Fourier Transform gives the cartesian density of states for a set of atoms.

    In a molecular system that would be made of non interacting particles, the velocities would be constant 
    at any time giving a VACF of constant value. In the gas-phase, the magnitude and direction of the velocity of a particle 
    will change gradually over time due collisions with other particles. In this case, the VACF is represented by a decaying exponential.
    
    In the solid phase, the interactions are much stronger and, as a result, the atoms are bound to a given, equilibrium position from 
    which they move backwards and forwards.  The oscillations are not be of equal magnitude however, but decay in time, because there are 
    anharmonic, perturbative forces which disrupt the oscillatory motion. In this case, the VACF looks like a damped harmonic motion.
    
    In the liquid phase, the atoms have more freedom than in the solid phase and because of the diffusion process, the oscillatory motion 
    seen in solid phase is damped rapidly depending on the density of the system. So, the VACF tends to have one very damped oscillation 
    before decaying to zero. The decaying time can be considered as the average time for a collision between two atoms.
    
    As well as revealing the dynamical processes in a system, the VACF has other interesting properties. Firstly, its Fourier transform, 
    a.k.a as vibrational Density Of States (vDOS) can be used to reveal the underlying frequencies of the molecular processes. This is closely 
    related to the infra-red spectrum of the system, which is also concerned with vibration on the molecular scale. Secondly, provided the VACF 
    decays to zero at long time, the function may be integrated mathematically to calculate the diffusion coefficient D, as in: 

    .. math:: D = \\frac{1}{3}\int_{0}^{+\infty}{<v(0) \cdot v(t)>dt}

    This is a special case of a more general relationship between the VACF and the mean square displacement, and belongs to a class of properties 
    known as the Green-Kubo relations, which relate correlation functions to so-called transport coefficients. 
    """

    type = 'vacf'
    
    label = "Velocity AutoCorrelation Function"

    category = ('Analysis','Dynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

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
                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
        
    