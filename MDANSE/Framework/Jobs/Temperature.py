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

@author: Eric C. Pellegrini
'''

import collections

import numpy

from MMTK import Units

from MDANSE import ELEMENTS
from MDANSE.Mathematics.Signal import differentiate
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory, sorted_atoms

class Temperature(IJob):
    """
    Computes the time-dependent temperature for a given trajectory.
    """

    type = 'temp'
    
    label = "Temperature"

    category = ('Thermodynamics',)
    
    ancestor = "mmtk_trajectory"
            
    configurators = collections.OrderedDict()
    configurators['trajectory'] = ('mmtk_trajectory',{})
    configurators['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    configurators['interpolation_order'] = ('interpolation_order', {'label':"velocities", 'dependencies':{'trajectory':'trajectory'}})
    configurators['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        
        self.numberOfSteps = self.configuration['trajectory']['instance'].universe.numberOfAtoms()
        
        self._nFrames = self.configuration['frames']['number']

        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')
        self._outputData.add("kinetic_energy","line", (self._nFrames,), axis="time",units='kJ_per_mole')
        self._outputData.add("temperature","line", (self._nFrames,), axis='time',units='K')
                                
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. kineticEnergy (numpy.array): The calculated kinetic energy
        """
        
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)

        atom = atoms[index]

        symbol = atom.symbol
                                                                                    
        mass = ELEMENTS[symbol,'atomic_weight']
                
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       [atom],
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       variable=self.configuration['interpolation_order']["variable"])
             
        order = self.configuration["interpolation_order"]["value"]
        
        if order != -1:
            for axis in range(3):
                series[:,axis] = differentiate(series[:,axis], order=order, dt=self.configuration['frames']['time_step'])
        
        kineticEnergy = 0.5*mass*numpy.sum(series**2,1)
                                                                                                                   
        return index, kineticEnergy
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["kinetic_energy"] += x
                                    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        
        fact = 3.0*Units.k_B*(self.configuration['trajectory']['instance'].universe.numberOfAtoms()-1)
                        
        self._outputData['temperature'][:] = 2.0*Units.eV*self._outputData['kinetic_energy']/fact
                        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self.header)
        
        self.configuration['trajectory']['instance'].close()     
  
        
