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
Created on Jun 15, 2018

:author: Eric C. Pellegrini
'''

import collections
import os

import numpy

from MMTK import Units
from MMTK.PDB import PDBConfiguration
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Extensions import xtc
from MDANSE.Framework.Jobs.Converter import Converter

class GromacsConverter(Converter):
    """
    Converts a Gromacs trajectory to a MMTK trajectory.
    """
                  
    label = "Gromacs"

    settings = collections.OrderedDict()           
    settings['pdb_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Gromacs','md.pdb')})
    settings['xtc_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Gromacs','md.xtc')})
    settings['fold'] = ('boolean', {'default':False,'label':"Fold coordinates in to box"})    
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        self._xtcFile = xtc.XTCTrajectoryFile(self.configuration["xtc_file"]["filename"],"r")

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xtcFile)
        
        # Create all objects from the PDB file.  
        conf = PDBConfiguration(self.configuration['pdb_file']['filename'])

        # Creates a collection of all the chemical objects stored in the PDB file
        molecules = conf.createAll()

        self._universe = ParallelepipedicPeriodicUniverse()
                                            
        # The chemical objects found in the PDB file introduced into the universe.
        self._universe.addObject(molecules)
        
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w')

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        # The x, y and z values of the current frame.
        coords,times,steps,box = self._xtcFile.read(1)
        
        conf = Configuration(self._universe,coords[0,:,:])
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        self._universe.setShape(box[0,:,:])
        
        self._universe.setConfiguration(conf)
        
        if self.configuration['fold']["value"]:        
            self._universe.foldCoordinatesIntoBox()
                                                   
        # The current time.
        t = times[0]*Units.ps

        # Store a snapshot of the current configuration in the output trajectory.
        self._snapshot(data={'time': t})
                                        
        return index, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x:
        @type x: any.
        """

        pass

    def finalize(self):
        """
        Finalize the job.
        """
        
        self._xtcFile.close()

        # Close the output trajectory.
        self._trajectory.close()
        
REGISTRY['gromacs'] = GromacsConverter
