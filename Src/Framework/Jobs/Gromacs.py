# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Gromacs.py
# @brief     Implements module/class/test Gromacs
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
    settings['pdb_file'] = ('input_file',{'wildcard':'PDB files (*.pdb)|*.pdb|All files|*',
                                            'default':os.path.join('..','..','..','Data','Trajectories','Gromacs','md.pdb')})
    settings['xtc_file'] = ('input_file',{'wildcard':'XTC files (*.xtc)|*.xtc|TRR files (*.trr)|*.trr|All files|*',
                                            'default':os.path.join('..','..','..','Data','Trajectories','Gromacs','md.xtc')})
    settings['fold'] = ('boolean', {'default':False,'label':"Fold coordinates in to box"})    
    settings['output_files'] = ('output_files', {'formats':["netcdf"],'root':'pdb_file'})
                
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
