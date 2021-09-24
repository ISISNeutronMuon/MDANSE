# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Castep.py
# @brief     Implements module/class/test Castep
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import itertools
import re

import numpy

from Scientific.Geometry import Vector

from MMTK import Atom
from MMTK import Units
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter


class CASTEPError(Error):
    pass


class MDFile(dict):
    """
    Class representing a .md file format (documentation can be found at
    https://www.tcm.phy.cam.ac.uk/castep/MD/node13.html). It is used to determine the structure of the file (eg. the
    length of each section) and to read the information stored in one frame of the trajectory.
    """
    
    def __init__(self, filename):
        """
        :param filename: The path to the .md file.
        :type filename: str
        """

        self['instance'] = open(filename, 'rb')  # Open the provided file.

        # Skip over the header
        while True:
            line = self["instance"].readline()
            if re.search('END', line):  # If the current line is the 'END header' line
                self["instance"].readline()  # Skip this line (it should be blank line)
                break  # At this point, the file handle should be at the line storing time information.
        
        self._headerSize = self["instance"].tell()  # Record the length of the header

        # Prepare a variable storing information about a non-specific frame.
        self._frameInfo = {"time_step": [0], "cell_data": [], "data": []}
                
        self["instance"].readline()  # Skip the line storing time information.
        # Save the length of the line storing time information
        self._frameInfo["time_step"].append(self["instance"].tell() - self._headerSize)
                
        while True:
            
            prevPos = self["instance"].tell()

            line = self["instance"].readline().strip()
            
            # If the properties of the cell data have not been determined yet and the current line documents cell data
            if not self._frameInfo["cell_data"] and re.match(".*<-- h$", line):
                # Save how far (in character number) the cell data is from the start of the frame
                self._frameInfo["cell_data"].append(prevPos - self._headerSize)
                # Skip the next two lines since cell data is always three lines long
                self["instance"].readline()
                self["instance"].readline()
                # Save the length of the cell data
                self._frameInfo["cell_data"].append(self["instance"].tell() - self._frameInfo["cell_data"][0] -
                                                    self._headerSize)
                
            # If the properties of the positional data have not been stored yet and the line stores this data
            elif not self._frameInfo["data"] and re.match(".*<-- R$", line):
                # Save how far (in character number) the positional data is from the start of the frame
                self._frameInfo["data"].append(prevPos - self._headerSize)
                            
            if not line:
                # Save the length of a frame minus one line of ionic data
                self._frameInfo["data"].append(prevPos - self._frameInfo["data"][0] - self._headerSize)
                break

        # Save the length of the frame, including a blank line
        self._frameSize = self["instance"].tell() - self._headerSize

        # Read the whole ionic data block (positions, velocities, and forces) of the first frame
        self["instance"].seek(self._headerSize + self._frameInfo["data"][0])
        frame = self["instance"].read(self._frameInfo["data"][1]).splitlines()
        self["n_atoms"] = len(frame)/3  # Save the number of atoms (length of positional data)

        # Create a list storing the chemical symbol of the element described on each line of positional data
        tmp = [f.split()[0] for f in frame[:self["n_atoms"]]]
        # Save a list of tuples where each tuple consists of the symbol on the amount of those atoms in the simulation
        self["atoms"] = [(element, len(list(group))) for element, group in itertools.groupby(tmp)]
                                                    
        self["instance"].seek(0, 2)  # Move file handle to the end of the file
        self["n_frames"] = (self['instance'].tell()-self._headerSize)/self._frameSize  # Save the number of frames
        self["instance"].seek(0)  # Move file handle to the beginning of the file
        
    def read_step(self, step):
        """
        Extracts data from one frame of the trajectory

        :param step: The number of the frame to be read.
        :type step: int

        :return: The time of the chosen frame, the cell vectors, and the positions of all atoms in three different units
        :rtype: (float, tuple, numpy.array)-tuple
        """
        
        start = self._headerSize+step*self._frameSize  # Determine where the step-th frame starts in the file

        # Move file handle to the starts of the line storing the information about time
        self['instance'].seek(start+self._frameInfo["time_step"][0])

        # Read the time stored in the line and convert its units
        timeStep = float(self['instance'].read(self._frameInfo["time_step"][1]))
        timeStep *= Units.hbar/Units.Hartree

        # Read and process the cell data
        self['instance'].seek(start+self._frameInfo["cell_data"][0])  # Move to the start of cell data
        basisVectors = self['instance'].read(self._frameInfo["cell_data"][1]).splitlines()  # Read the cell data by line
        # Generate a tuple of three vectors where each vector is constructed from its components stored in each line
        basisVectors = tuple([Vector([float(bb) for bb in b.strip().split()[:3]])*Units.Bohr for b in basisVectors])
        
        self['instance'].seek(start+self._frameInfo["data"][0])  # Move to the start of positional data
        # Create an array composed of the data points in each line of the positional data
        config = numpy.array(self['instance'].read(self._frameInfo["data"][1]).split(), dtype=str)
        config = numpy.reshape(config, (3*self["n_atoms"], 7))  # Reshape the 1D array so that it is organised by lines
        config = config[:, 2:5].astype(numpy.float64)  # Extract the coordintates only

        # Convert the units of the positions
        config[0:self["n_atoms"], :] *= Units.Bohr
        config[self["n_atoms"]:2*self["n_atoms"], :] *= Units.Bohr*Units.Hartree/Units.hbar
        config[2*self["n_atoms"]:3*self["n_atoms"], :] *= Units.Hartree/Units.Bohr
        
        return timeStep, basisVectors, config

    def close(self):
        """Closes the file."""
        self["instance"].close()


class CASTEPConverter(Converter):
    """
    Converts a Castep Trajectory into a MMTK trajectory file. 
    """
    
    label = "CASTEP"
        
    settings = collections.OrderedDict()
    settings['castep_file'] = ('input_file', {'default': os.path.join('..', '..', '..', 'Data', 'Trajectories',
                                                                      'CASTEP', 'PBAnew.md')})
    settings['output_files'] = ('output_files', {'formats': ["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self._castepFile = MDFile(self.configuration["castep_file"]["filename"])  # Create a representation of md file
        
        self.numberOfSteps = self._castepFile["n_frames"]  # Save the number of steps

        self._universe = ParallelepipedicPeriodicUniverse()  # Create a bound universe

        # Populate the universe with atoms based on how many of each atom is in the read trajectory
        for symbol, number in self._castepFile["atoms"]:
            for i in range(number):
                self._universe.addObject(Atom(symbol, name="%s_%d" % (symbol, i)))
                
        self._universe.initializeVelocitiesToTemperature(0.)
        self._velocities = ParticleVector(self._universe)

        self._gradients = ParticleVector(self._universe)        

        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w')

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions=[TrajectoryOutput(self._trajectory, ["all"],
                                                                                     0, None, 1)])
    
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        :return: The index of the step and None
        :rtype: (int, None)-tuple

        @note: the argument index is the index of the loop not the index of the frame.
        """
                
        nAtoms = self._castepFile["n_atoms"]  # Retrieve the number of atoms
        
        timeStep, basisVectors, config = self._castepFile.read_step(index)  # Read the informatino in the frame
        
        self._universe.setShape(basisVectors)  # Set the boundaries of the universe using the cell vectors
            
        conf = Configuration(self._universe, config[0:nAtoms, :])
        
        self._universe.setConfiguration(conf)
                   
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time": timeStep}

        # Retrieve the positions multiplied by Units.Bohr*Units.Hartree/Units.hbar and save them as universe velocities
        self._velocities.array = config[nAtoms:2*nAtoms, :]
        self._universe.setVelocities(self._velocities)

        # Retrieve the positions multiplied by Units.Hartree/Units.Bohr and save them
        self._gradients.array = config[2*nAtoms:3*nAtoms, :]
        data["gradients"] = self._gradients

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
        
        self._castepFile.close()  # Close the .md file.

        # Close the output trajectory.
        self._trajectory.close()


REGISTRY['castep'] = CASTEPConverter
        
