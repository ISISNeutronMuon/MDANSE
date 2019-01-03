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

HARTREE_TIME = Units.hbar/Units.Hartree

class CASTEPError(Error):
    pass

class MDFile(dict):
    
    def __init__(self, filename):
        
        self['instance'] = open(filename, 'rb')
        for _ in range(5):
            self["instance"].readline()
        
        self._headerSize = self["instance"].tell()
                
        self._frameInfo = {"time_step":[0], "cell_data":[], "data" : []}
                
        line = self["instance"].readline()
        self._frameInfo["time_step"].append(self["instance"].tell() - self._headerSize)
                
        while True:
            
            prevPos = self["instance"].tell()

            line = self["instance"].readline().strip()
            
            if not self._frameInfo["cell_data"] and re.match(".*<-- h$",line):
                self._frameInfo["cell_data"].append(prevPos - self._headerSize)
                self["instance"].readline()
                self["instance"].readline()
                self._frameInfo["cell_data"].append(self["instance"].tell() - self._frameInfo["cell_data"][0] - self._headerSize)
                
            elif not self._frameInfo["data"] and re.match(".*<-- R$",line):
                self._frameInfo["data"].append(prevPos - self._headerSize)
                            
            if not line:
                self._frameInfo["data"].append(prevPos - self._frameInfo["data"][0] - self._headerSize) 
                break

        self._frameSize = self["instance"].tell() - self._headerSize
        
        self["instance"].seek(self._headerSize + self._frameInfo["data"][0])
        frame = self["instance"].read(self._frameInfo["data"][1]).splitlines()
        self["n_atoms"] = len(frame)/3
        tmp = [f.split()[0] for f in frame[:self["n_atoms"]]]
        self["atoms"] = [(element,len(list(group))) for element,group in itertools.groupby(tmp)]
                                                    
        self["instance"].seek(0,2)           
        
        self["n_frames"] = (self['instance'].tell()-self._headerSize)/self._frameSize
        
        self["instance"].seek(0)           
        
    def read_step(self, step):
        """
        """
        
        start = self._headerSize+step*self._frameSize
        
        self['instance'].seek(start+self._frameInfo["time_step"][0])
        
        timeStep = float(self['instance'].read(self._frameInfo["time_step"][1]))
        timeStep *= Units.hbar/Units.Hartree
        
        self['instance'].seek(start+self._frameInfo["cell_data"][0])
        basisVectors = self['instance'].read(self._frameInfo["cell_data"][1]).splitlines()
        basisVectors = tuple([Vector([float(bb) for bb in b.strip().split()[:3]])*Units.Bohr for b in basisVectors])
        
        self['instance'].seek(start+self._frameInfo["data"][0])
        config = numpy.array(self['instance'].read(self._frameInfo["data"][1]).split(),dtype=str)
        config = numpy.reshape(config,(3*self["n_atoms"],7))
        config = config[:,2:5].astype(numpy.float64)
        
        config[0:self["n_atoms"],:] *= Units.Bohr        

        config[self["n_atoms"]:2*self["n_atoms"],:] *= Units.Bohr*Units.Hartree/Units.hbar      
        
        config[2*self["n_atoms"]:3*self["n_atoms"],:] *= Units.Hartree/Units.Bohr
        
        return timeStep, basisVectors, config

    def close(self):
        self["instance"].close()

class CASTEPConverter(Converter):
    """
    Converts a Castep Trajectory into a MMTK trajectory file. 
    """
    
    label = "CASTEP"
        
    settings = collections.OrderedDict()
    settings['castep_file'] = ('input_file', {'default':os.path.join('..','..','..','Data','Trajectories','CASTEP','PBAnew.md')})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self._castepFile = MDFile(self.configuration["castep_file"]["filename"])
        
        self.numberOfSteps = self._castepFile["n_frames"]

        self._universe = ParallelepipedicPeriodicUniverse()

        for symbol,number in self._castepFile["atoms"]:
            for i in range(number):
                self._universe.addObject(Atom(symbol, name="%s_%d" % (symbol,i)))
                
        self._universe.initializeVelocitiesToTemperature(0.)
        self._velocities = ParticleVector(self._universe)

        self._gradients = ParticleVector(self._universe)        

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
                
        nAtoms = self._castepFile["n_atoms"]
        
        timeStep, basisVectors, config = self._castepFile.read_step(index)
        
        self._universe.setShape(basisVectors)
            
        conf = Configuration(self._universe, config[0:nAtoms,:])
        
        self._universe.setConfiguration(conf)
                   
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time" : timeStep}
        
        self._velocities.array = config[nAtoms:2*nAtoms,:]
        self._universe.setVelocities(self._velocities)

        self._gradients.array = config[2*nAtoms:3*nAtoms,:]
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
        
        self._castepFile.close()

        # Close the output trajectory.
        self._trajectory.close()

REGISTRY['castep'] = CASTEPConverter
        
