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
import os

from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.PDB import PDBFile
from MMTK.ParticleProperties import Configuration

from MDANSE.Framework.Jobs.Converters.Converter import Converter

class PDBConverter(Converter):
    """
    Converts a PDB trajectory to a MMTK trajectory.
    """
    type = 'pdb'
    
    label = "PDB"

    category = ('Converters',)
    
    ancestor = []

    settings = collections.OrderedDict()  
    settings['pdb_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','PDB','2f58_nma.pdb')})
    settings['nb_frame'] = ('range', {'valueType':int, 'includeLast':True, 'mini':0.0, 'default':(0,2,1)})
    settings['time_step'] = ('float', {'mini':1.0e-6, 'default':1.0})
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
     
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        # The indices of frames which should be extacted from pdb file 
        self.frame_list = self.configuration['nb_frame']["value"]
        self.numberOfSteps = self.configuration['nb_frame']["number"]

        # Create all objects from the PDB file.  
        pdb_config = PDBFile(self.configuration['pdb_file']['filename'], model=0)

        # Create the universe.
        self._universe = pdb_config.createUnitCellUniverse()
                
        # Construct system
        self._universe.addObject(pdb_config.createAll(None, 1))
        
        # Open the new trajectory 
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], "w", "Converted from PDB")
        
        # Make a snapshot generator for saving.
        self._snapshot = SnapshotGenerator(self._universe,actions = [TrajectoryOutput(self._trajectory, None, 0, None, 1)])
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
        """
    
        frame = self.frame_list[index]
        
        pdb_config = PDBFile(self.configuration['pdb_file']['filename'], model=frame)
        uni = pdb_config.createUnitCellUniverse()
        uni.addObject(pdb_config.createAll(None, 1))
                
        univ_config  = Configuration(self._universe, uni.configuration().array)
        
        self._universe.setConfiguration(univ_config)
        self._universe.foldCoordinatesIntoBox()
        self._snapshot(data = {'time':frame})

        return index, None
    
    def combine(self, index, x):
        """
        Not used here
        """   
        pass
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 
        # Close the output trajectory.
        self._trajectory.close()
