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

import numpy

from MMTK.Collections import Collection
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

class BoxCenteredTrajectory(IJob):
    """
    Build a new trajectory by translating the contents of the simulation box such that a given atom selection is at the centre of the simulation box. 
    """
    
    type = 'btt'
    
    label = "Box Translated Trajectory"

    category = ('Analysis','Trajectory',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection',{'dependencies':{'trajectory':'trajectory'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the analysis (open trajectory, create output variables ...)
        """

        self.numberOfSteps = self.configuration['frames']['number']
        
        self._universe = self.configuration['trajectory']['instance'].universe

        # Create a MMTK collection from the atoms selected for translation.
        atoms = sorted_atoms(self.configuration['trajectory']['instance'].universe)
        self._selectedAtoms = Collection([atoms[ind] for ind in self.configuration['atom_selection']['indexes']])
                        
        # The output trajectory is opened for writing.
        self._btt = Trajectory(self._selectedAtoms, self.configuration['output_files']['files'][0], "w")        
        self._btt.title = self.__class__.__name__
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._btt, "all", 0, None, 1)])

        # This will store the box coordinates of the previous configuration
        self._boxCoords = None

    def run_step(self, index):
        """
        Runs a single step of the analysis.
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. None
        """

        # Get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
              
        # The configuration corresponding to this index is set to the universe.
        self._universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)

        # Get a contiguous copy of the current configuration.
        conf = self._universe.contiguousObjectConfiguration()

        # For the first step, the box coordinates are just set to the box coordinates of the current configuration.
        if self._boxCoords is None:            
            self._boxCoords = self._universe._realToBoxPointArray(conf.array)
            
        # For the other step, the box coordinates are set equal to the configuration corrected from box jumps. 
        else:
            
            currBoxCoords = self._universe._realToBoxPointArray(conf.array)
            diff = currBoxCoords - self._boxCoords
            self._boxCoords = currBoxCoords - numpy.round(diff)
        
        # A new configuration is made from the box coordinates set back to real coordinates.
        conf = Configuration(self._universe, self._universe._boxToRealPointArray(self._boxCoords))
        
        # The universe is translated by the center of the selected atoms.
        c = center(conf.array[self.configuration['atom_selection']['indexes'],:])
        conf.array -= c                        
        self._universe.setConfiguration(conf)
    
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # The current configuration is written to the output trajectory.
        self._snapshot(data = {'time': t})
                                
        return index, None
        
    def combine(self, index, x):
        """
        Update the output each time a step is performed
        
        :Parameters:
            #. index (int): The index of the step.
            #. x (any): The returned result(s) of run_step
        """
        pass
        
    def finalize(self):
        """
        Finalize the analysis (close trajectory, write output data ...)
        """

        # The input trajectory is closed.
        self.configuration['trajectory']['instance'].close()
                                                    
        # The output trajectory is closed.
        self._btt.close()   
