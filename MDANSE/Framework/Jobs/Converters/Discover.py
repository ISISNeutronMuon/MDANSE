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

import os
import collections

import struct

import numpy

from MMTK import Units
from MMTK.ParticleProperties import Configuration, ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput

from MDANSE.Framework.Jobs.Converters.Converter import Converter
from MDANSE.Framework.Jobs.Converters.MaterialsStudio import XTDFile

class HisFile(dict):

    def __init__(self, hisfilename):
                
        self['instance'] = open(hisfilename, "rb")
        
        self.parse_header()
        
    def parse_header(self):
        
        hisfile = self['instance']
        
        # Record 1
        rec = "!4x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)
        
        rec = "!i8x"
        self._rec1Size = struct.calcsize(rec)
        rec,hisfile.read(self._rec1Size)
                        
        # Record 2
        rec = "!80sd8x"
        recSize = struct.calcsize(rec)
        VERSION_INFO,VERSION = struct.unpack(rec,hisfile.read(recSize))
        VERSION_INFO = VERSION_INFO.strip()

        # Record 3+4
        rec = "!80s8x80s8x"
        recSize = struct.calcsize(rec)
        self["title"] = struct.unpack(rec,hisfile.read(recSize))
        self["title"] = "\n".join(self["title"])

        # Record 5
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_ATTYP = struct.unpack(rec,hisfile.read(recSize))[0]
        rec = "!" + "%ds" % (4*N_ATTYP) + "%dd" % N_ATTYP + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 6
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_NMRES = struct.unpack(rec,hisfile.read(recSize))[0]
        rec = "!" + "%ds" % (4*N_NMRES) + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)
        
        # Record 7
        rec = "!i"
        recSize = struct.calcsize(rec)
        self["n_atoms"] = N_ATOMS = struct.unpack(rec,hisfile.read(recSize))[0]
        rec = "!" + "%di" % N_ATOMS
        if VERSION < 2.9:
            rec += "%ds" % (4*N_ATOMS)
        else:
            rec += "%ds" % (5*N_ATOMS)
        rec += "8x"            
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 8
        rec = "!ii"
        recSize = struct.calcsize(rec)
        _, N_MOVAT = struct.unpack(rec,hisfile.read(recSize))
        if VERSION >= 2.6:
            rec = "!" + "%di" % N_MOVAT
            recSize = struct.calcsize(rec)
            self["movable_atoms"] = numpy.array(struct.unpack(rec,hisfile.read(recSize)), dtype=numpy.int32) - 1
        else:
            self["movable_atoms"] = range(self["n_atoms"])
        rec = "!8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)
        
        # Record 9
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_MOL = struct.unpack(rec,hisfile.read(recSize))[0]
        rec = "!" + "%di" % N_MOL + "%di" % N_MOL + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)
        
        # Record 10
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_RES = struct.unpack(rec,hisfile.read(recSize))[0]
        rec = "!" + "%di" % (2*N_RES) + "%di" % N_RES + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 11
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_BONDS = struct.unpack(rec,hisfile.read(recSize))[0]
        if N_BONDS > 0:
            rec = "!" + "%di" % (2*N_BONDS)
            recSize = struct.calcsize(rec)
            _ = struct.unpack(rec,hisfile.read(recSize))
        rec = "!8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 12
        rec = "!6d"
        recSize = struct.calcsize(rec)
        _ = struct.unpack(rec,hisfile.read(recSize))
        rec = "!9d"
        recSize = struct.calcsize(rec)
        self["initial_cell"] = numpy.reshape(numpy.array(struct.unpack(rec,hisfile.read(recSize)),dtype=numpy.float64),(3,3))*Units.Ang
        
        rec = "!4134di4di6d6i8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)
        
        # Record 13
        rec = "!idii8x"
        recSize = struct.calcsize(rec)
        N_ENER, TIME_STEP, _, _ = struct.unpack(rec,hisfile.read(recSize))
        self["time_step"] = TIME_STEP*Units.fs

        # Record 14
        rec = "!3d" + "%dd" % N_ENER + "%dd" % N_MOL + "%dd" % (N_MOL*N_ENER) + "%dd" % (4*N_MOL+2+54) + "8x"
        self._rec14Size = struct.calcsize(rec)
        hisfile.read(self._rec14Size)

        # Record 15
        rec = "!" + "%df" % (3*N_ATOMS) + "8x"
        recSize = struct.calcsize(rec)
        self["initial_coordinates"] = numpy.reshape(struct.unpack(rec,hisfile.read(recSize)),(N_ATOMS,3))
            
        # Record 16
        rec = "!" + "%df" % (3*N_ATOMS) + "8x"
        recSize = struct.calcsize(rec)
        self["initial_velocities"] = numpy.reshape(struct.unpack(rec,hisfile.read(recSize)),(N_ATOMS,3))

        self._headerSize = hisfile.tell()
                                
        self._recN2 = "!15d8x"
        self._recN2Size = struct.calcsize(self._recN2)
                                
        if VERSION < 2.6:
            self["n_movable_atoms"] = N_ATOMS
        else:
            self["n_movable_atoms"] = N_MOVAT
        self._recCoord = "!" + "%df" % (3*self["n_movable_atoms"]) + "8x"
        self._recCoordSize = struct.calcsize(self._recCoord)
        self._recVel = "!" + "%df" % (3*self["n_movable_atoms"]) + "8x"
        self._recVelSize = struct.calcsize(self._recVel)
        
        self._frameSize = self._rec1Size + self._rec14Size + self._recN2Size + self._recCoordSize + self._recVelSize

        hisfile.seek(0,2)
        
        self["n_frames"] = (hisfile.tell()-self._headerSize)/self._frameSize
                
    def read_step(self, index):
        
        hisfile = self["instance"]
        
        time = index*self["time_step"]
        
        hisfile.seek(self._headerSize + index*self._frameSize + self._rec1Size + self._rec14Size)
        
        cell = numpy.reshape(numpy.array(struct.unpack(self._recN2,hisfile.read(self._recN2Size))[6:]),(3,3))*Units.Ang
        
        coords = numpy.reshape(struct.unpack(self._recCoord,hisfile.read(self._recCoordSize)),(self["n_movable_atoms"],3))
        coords *= Units.Ang
        
        vels = numpy.reshape(struct.unpack(self._recVel,hisfile.read(self._recVelSize)),(self["n_movable_atoms"],3))
        vels *= Units.Ang/Units.fs
        
        return time, cell, coords, vels
        
    def close(self):
        self["instance"].close()
        
class DiscoverConverter(Converter):
    """
    Converts a Discover trajectory to a MMTK trajectory.
    """

    type = 'discover'
    
    label = "Discover"

    category = ('Converters',)
    
    ancestor = None

    settings = collections.OrderedDict()
    settings['xtd_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Discover','sushi.xtd')})
    settings['his_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Discover','sushi.his')})
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
    
    def initialize(self):
        '''
        Initialize the job.
        '''
        
        self._xtdfile = XTDFile(self.configuration["xtd_file"]["filename"])
        
        self._xtdfile.build_universe()
        
        self._universe = self._xtdfile.universe
        
        self._hisfile = HisFile(self.configuration["his_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._hisfile['n_frames']
                             
        if self._universe.is_periodic:
            self._universe.setShape(self._hisfile['initial_cell'])

        conf = Configuration(self._universe, self._hisfile["initial_coordinates"])
        self._universe.setConfiguration(conf)        
                             
        self._universe.initializeVelocitiesToTemperature(0.)
        self._velocities = ParticleVector(self._universe)
        self._velocities.array = self._hisfile["initial_velocities"]
        self._universe.setVelocities(self._velocities)
        
        self._universe.foldCoordinatesIntoBox()
            
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], mode='w', comment=self._hisfile["title"])

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])
        
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
                                                
        # The x, y and z values of the current frame.
        time, cell, config, vel = self._hisfile.read_step(index)
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        if self._universe.is_periodic:
            self._universe.setShape(cell)
            
        movableAtoms = self._hisfile['movable_atoms']
            
        self._universe.configuration().array[movableAtoms,:] = config
                   
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time" : time}
        
        self._velocities.array[movableAtoms,:] = vel
        self._universe.setVelocities(self._velocities)

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
        
        self._hisfile.close()

        # Close the output trajectory.
        self._trajectory.close()