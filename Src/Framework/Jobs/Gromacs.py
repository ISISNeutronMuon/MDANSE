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
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Extensions import xtc, trr
from MDANSE.Framework.Jobs.Converter import Converter


class GromacsConverterError(Error):
    pass


class GromacsConverter(Converter):
    """
    Converts a Gromacs trajectory to a MMTK trajectory.
    """
                  
    label = "Gromacs"

    settings = collections.OrderedDict()           
    settings['pdb_file'] = ('input_file',
                            {'default': os.path.join('..','..','..','Data','Trajectories','Gromacs','md.pdb')})
    settings['xtc_file'] = ('input_file',
                            {'default': os.path.join('..','..','..','Data','Trajectories','Gromacs','md.xtc'),
                             'label': 'xtc or trr file'})
    settings['fold'] = ('boolean', {'default':False,'label':"Fold coordinates in to box"})    
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        '''
        Initialize the job.
        '''

        # Create XTC or TRR object depending on which kind of trajectory was loaded
        if self.configuration["xtc_file"]["filename"][-4:] == '.xtc':
            self._xdr_file = xtc.XTCTrajectoryFile(self.configuration["xtc_file"]["filename"], "r")
            self._xtc = True
        elif self.configuration["xtc_file"]["filename"][-4:] == '.trr':
            self._xdr_file = trr.TRRTrajectoryFile(self.configuration["xtc_file"]["filename"], "r")
            self._xtc = False

            # Extract information about whether velocities and forces are present in the TRR file
            try:
                self._read_velocities = self._xdr_file.has_velocities
                self._read_forces = self._xdr_file.has_forces
            except AttributeError:
                self._read_velocities, self._read_forces = self._xdr_file._check_has_velocities_forces()
                if self._read_velocities < 0 or self._read_forces < 0:
                    raise RuntimeError("Could not determine whether velocities or forces are present!")

            # The TRRTrajectoryFile object returns ints for these values, so turn them into bools
            self._read_velocities, self._read_forces = bool(self._read_velocities), bool(self._read_forces)
        else:
            raise GromacsConverterError('Invalid file format: Gromacs converter can only convert XTC and TRR files, '
                                        'but %s was provided.' % self.configuration["xtc_file"]["filename"][-4:])

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xdr_file)
        
        # Create all objects from the PDB file.  
        conf = PDBConfiguration(self.configuration['pdb_file']['filename'])

        # Creates a collection of all the chemical objects stored in the PDB file
        molecules = conf.createAll()
                                            
        # Create a universe and introduce dhe chemical objects found in the PDB file into the universe.
        self._universe = ParallelepipedicPeriodicUniverse()
        self._universe.addObject(molecules)

<<<<<<< HEAD
        data_to_be_written = ['configuration','time']
=======
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1
        # If a TRR trajectory is being read, initialise velocities and forces
        if not self._xtc:
            if self._read_velocities:
                self._universe.initializeVelocitiesToTemperature(0.)
                self._velocities = ParticleVector(self._universe)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> The coords, velocities and forces arrays are now casted to float64
                data_to_be_written.append('velocities')
            if self._read_forces:
                self._forces = ParticleVector(self._universe)
                data_to_be_written.append('gradients')
<<<<<<< HEAD
=======
            if self._read_forces:
                self._forces = ParticleVector(self._universe)
>>>>>>> Enable reading trr files not containing vels/forces
=======
>>>>>>> The coords, velocities and forces arrays are now casted to float64
=======
            if self._read_forces:
                self._forces = ParticleVector(self._universe)
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1

        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w')

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe,
<<<<<<< HEAD
                                           actions = [TrajectoryOutput(self._trajectory, data_to_be_written, 0, None, 1)])
=======
                                           actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        # The x, y and z values of the current frame.
        if self._xtc:
            coords, times, steps, box = self._xdr_file.read(1)
        else:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(1,
                                                                                    get_velocities=self._read_velocities,
                                                                                    get_forces=self._read_forces)
=======
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(1)
>>>>>>> Remove problematic double import and unpack correctly
=======
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(1,
                                                                                    get_velocities=self._read_velocities,
                                                                                    get_forces=self._read_forces)
>>>>>>> Enable reading trr files not containing vels/forces
        
        conf = Configuration(self._universe, coords[0,:,:].astype(float))
=======
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(1,
                                                                                    get_velocities=self._read_velocities,
                                                                                    get_forces=self._read_forces)
        
        conf = Configuration(self._universe, coords[0,:,:])
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        self._universe.setShape(box[0,:,:])
        
        self._universe.setConfiguration(conf)

        if self.configuration['fold']["value"]:        
            self._universe.foldCoordinatesIntoBox()

        # The current time.
        t = times[0] * Units.ps
        data = {'time': t}

        # Set velocities and forces if available
        if not self._xtc:
            if self._read_velocities:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                self._velocities.array = velocities[0, :, :].astype(float)  # already in nm/ps
                data['velocities'] = self._velocities
            if self._read_forces:
                self._forces.array = forces[0, :, :].astype(float)  # already in kJ/(mol nm)
                data["gradients"] = self._forces
=======
=======
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1
                self._velocities.array = velocities[0, :, :]  # already in nm/ps
                self._universe.setVelocities(self._velocities)
            if self._read_forces:
                self._forces.array = forces[0, :, :]  # already in kJ/(mol nm)
                data["forces"] = self._forces
<<<<<<< HEAD
>>>>>>> Enable reading trr files not containing vels/forces
=======
                self._velocities.array = velocities[0, :, :].astype(float)  # already in nm/ps
                data['velocities'] = self._velocities
            if self._read_forces:
                self._forces.array = forces[0, :, :].astype(float)  # already in kJ/(mol nm)
                data["gradients"] = self._forces
>>>>>>> The coords, velocities and forces arrays are now casted to float64
=======
>>>>>>> 97f6c0563d27cc4e7f218c7f0554b461ab80efa1

        # Store a snapshot of the current configuration in the output trajectory.
        self._snapshot(data=data)
                                        
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
        
        self._xdr_file.close()

        # Close the output trajectory.
        self._trajectory.close()


REGISTRY['gromacs'] = GromacsConverter
