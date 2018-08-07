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

from MMTK import Units

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Externals.magnitude.magnitude import mg
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class Density(IJob):
    """
    Computes the atom and mass densities for a given trajectory. These are time dependent if the simulation box volume fluctuates.
    """
    
    label = "Density"

    category = ('Analysis','Thermodynamics',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def initialize(self):

        self.numberOfSteps = self.configuration['frames']['number']

        self._nFrames = self.numberOfSteps
        
        self._symbols = sorted_atoms(self.configuration['trajectory']['instance'].universe,"symbol")

        # Will store the time.
        self._outputData.add("time","line", self.configuration['frames']['time'], units='ps')

        self._outputData.add("mass_density","line", (self._nFrames,), axis='time', units='g/cm3')

        self._outputData.add("atomic_density","line", (self._nFrames,), axis='time', units='1/cm3')

        if not self.configuration['trajectory']['instance'].universe.is_periodic:
            raise JobError("Pair distribution function cannot be calculated for infinite universe trajectories")
                                
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
                        
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
                
        cellVolume = self.configuration['trajectory']['instance'].universe.cellVolume()*mg(1.0,'nm3','cm3').toval()
                
        atomicDensity = self.configuration['trajectory']['instance'].universe.numberOfAtoms()/cellVolume
                
        massDensity = sum([ELEMENTS[s,'atomic_weight'] for s in self._symbols])/Units.Nav/cellVolume
                        
        return index, (atomicDensity, massDensity)
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """
                                
        self._outputData["atomic_density"][index] = x[0]
        
        self._outputData["mass_density"][index] = x[1]
       
    def finalize(self):
        """
        Finalize the job.
        """        

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['den'] = Density
                                         