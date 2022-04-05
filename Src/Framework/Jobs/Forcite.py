# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Forcite.py
# @brief     Implements module/class/test Forcite
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import struct

import numpy

from MMTK import Units
from MMTK.ParticleProperties import ParticleVector
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Externals.magnitude.magnitude import mg
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.Framework.Jobs.MaterialsStudio import XTDFile

FORCE_FACTOR = mg(1.0,"kcal_per_mole/ang","uma nm/ps2").toval()

class TrjFile(dict):

    def __init__(self, trjfilename):
                
        self['instance'] = open(trjfilename, "rb")
        
        self.parse_header()
        
    def parse_header(self):
        
        trjfile = self['instance']
        
        rec = "!4x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)
        
        # Record 1
        rec = "!4s20i8x"
        recSize = struct.calcsize(rec)
        DATA = struct.unpack(rec,trjfile.read(recSize))
        VERSION = DATA[1]
        if VERSION < 2010:
            self._fp = "f"
        else:
            self._fp = "d"
            
        # Diff with doc --> NTRJTI and TRJTIC not in doc
        rec = '!i'
        recSize = struct.calcsize(rec)
        NTRJTI, = struct.unpack(rec, trjfile.read(recSize))
        rec = '!%ds8x' % (80*NTRJTI)
        recSize = struct.calcsize(rec)
        self["title"] = struct.unpack(rec, trjfile.read(recSize))
        self["title"] = "".join(self["title"])
        
        # Record 2
        rec = "!i"
        recSize = struct.calcsize(rec)
        NEEXTI = struct.unpack(rec,trjfile.read(recSize))[0]
        rec = "!" + "%ds" % (80*NEEXTI) + '8x'
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        # Record 3
        rec = "!8i8x"
        recSize = struct.calcsize(rec)
        PERTYPE,_,LCANON,DEFCEL,_,_,LNPECAN,LTMPDAMP = struct.unpack(rec,trjfile.read(recSize))
        self["pertype"] = PERTYPE
        self["defcel"] = DEFCEL

        # Record 4
        rec = "!i"
        recSize = struct.calcsize(rec)
        NFLUSD = struct.unpack(rec,trjfile.read(recSize))[0]

        rec = '!%di%di%ds8x' % (NFLUSD,NFLUSD,8*NFLUSD)
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        rec = '!i'
        recSize = struct.calcsize(rec)
        self["totmov"] = struct.unpack(rec,trjfile.read(recSize))[0]

        rec = '!%di8x' % self["totmov"]
        recSize = struct.calcsize(rec)
        self["mvofst"] = numpy.array(struct.unpack(rec,trjfile.read(recSize)), dtype=numpy.int32) - 1

        # Record 4a
        rec = "!i"
        recSize = struct.calcsize(rec)
        LEEXTI, = struct.unpack(rec,trjfile.read(recSize))
        rec = "!%ds8x" % LEEXTI
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)        
        
        # Record 4b
        rec = "!i"
        recSize = struct.calcsize(rec)
        LPARTI, = struct.unpack(rec,trjfile.read(recSize))
        rec = "!%ds8x" % LPARTI
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)        

        self._headerSize = trjfile.tell()

        # Frame record 1        
        if VERSION == 2000:
            rec1 = '!%si33%s5i8x' % (self._fp,self._fp)
        elif VERSION == 2010:
            rec1 = '!%si57%s6i8x' % (self._fp,self._fp)
        else:
            rec1 = '!%si58%s6i8x' % (self._fp,self._fp)

        recSize = struct.calcsize(rec1)
        DATA = struct.unpack(rec1,trjfile.read(recSize))
        
        if VERSION < 2010:
            self["velocities_written"] = DATA[-3]
            self["gradients_written"] = 0
        else:
            self["velocities_written"] = DATA[-4]
            self["gradients_written"] = DATA[-3]
        
        # Frame record 2        
        rec = '!12%s8x' % self._fp
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)
        
        # Frame record 3    
        if LCANON:
            rec = '!4%s8x' % self._fp
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)
        
        if PERTYPE > 0:
            # Frame record 4
            self._defCellRecPos = trjfile.tell() - self._headerSize
            self._defCellRec = '!22%s8x' % self._fp
            self._defCellRecSize = struct.calcsize(self._defCellRec)
            trjfile.read(self._defCellRecSize)

        if PERTYPE > 0:
            # Frame record 5
            rec = '!i14%s8x' % self._fp
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)

        if LNPECAN:
            # Frame record 6
            rec = '!3%s8x' % self._fp
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)
            
        if LTMPDAMP:
            # Frame record 7
            rec = '!%s8x' % self._fp
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)
            
        self._configRecPos = trjfile.tell() - self._headerSize
                    
        if self["velocities_written"]:
            if self["gradients_written"]:
                # Frame record 8,9,10,11,12,13,14,15,16
                self._configRec = '!' + ('%d%s8x'*9) % ((self['totmov'],self._fp)*9)
            else:
                # Frame record 8,9,10,11,12,13
                self._configRec = '!' + ('%d%s8x'*6) % ((self['totmov'],self._fp)*6)
        else:
            if self["gradients_written"]:
                # Frame record 8,9,10,14,15,16
                self._configRec = '!' + ('%d%s8x'*6) % ((self['totmov'],self._fp)*6)
            else:
                # Frame record 8,9,10
                self._configRec = '!' + ('%d%s8x'*3) % ((self['totmov'],self._fp)*3)

        self._configRecSize = struct.calcsize(self._configRec)
        trjfile.read(self._configRecSize)
        
        self._frameSize = trjfile.tell() - self._headerSize
        
        trjfile.seek(0,2)
        
        self["n_frames"] = (trjfile.tell()-self._headerSize)/self._frameSize
        
    def read_step(self, index):
        """
        """

        trjfile = self["instance"]

        pos = self._headerSize + index*self._frameSize
        
        trjfile.seek(pos,0)

        rec = '!%s' % self._fp
        recSize = struct.calcsize(rec)
        timeStep, = struct.unpack(rec,trjfile.read(recSize))
        
        if self["defcel"]:
            trjfile.seek(pos + self._defCellRecPos,0)
            cell = numpy.zeros((3,3),dtype=numpy.float64)
            # ax,by,cz,bz,az,ay            
            cellData = numpy.array(struct.unpack(self._defCellRec,trjfile.read(self._defCellRecSize)),dtype=numpy.float64)[2:8]*Units.Ang
            cell[0,0] = cellData[0]
            cell[1,1] = cellData[1]
            cell[2,2] = cellData[2]
            cell[1,2] = cellData[3]
            cell[0,2] = cellData[4]
            cell[0,1] = cellData[5]
            
        else:
            cell = None

        trjfile.seek(pos + self._configRecPos,0)
        
        config = struct.unpack(self._configRec,trjfile.read(self._configRecSize))
        
        if self["velocities_written"]:
            if self["gradients_written"]:
                config = numpy.transpose(numpy.reshape(config,(3,3, self['totmov'])))
                xyz    = config[:,:,0]*Units.Ang
                vel    = config[:,:,1]*Units.Ang
                gradients = config[:,:,2]*FORCE_FACTOR
            else:
                config = numpy.transpose(numpy.reshape(config,(2,3, self['totmov'])))
                xyz    = config[:,:,0]*Units.Ang
                vel    = config[:,:,1]*Units.Ang
                gradients = None
        else:
            if self["gradients_written"]:
                config = numpy.transpose(numpy.reshape(config,(2,3, self['totmov'])))
                xyz    = config[:,:,0]*Units.Ang
                vel    = None
                gradients = config[:,:,1]*FORCE_FACTOR
            else:
                config = numpy.transpose(numpy.reshape(config,(1,3, self['totmov'])))
                xyz    = config[:,:,0]*Units.Ang
                vel    = None
                gradients = None
            
        return timeStep, cell, xyz, vel, gradients

    def close(self):
        self["instance"].close()
        
class ForciteConverter(Converter):
    """
    Converts a Forcite trajectory to a MMTK trajectory.
    """
    
    label = "Forcite"

    category = ('Converters','Materials Studio')
    
    settings = collections.OrderedDict()
    settings['xtd_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Forcite','nylon66_rho100_500K_v300K.xtd')})
    settings['trj_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','Forcite','nylon66_rho100_500K_v300K.trj')})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        '''
        Initialize the job.
        '''
        
        self._xtdfile = XTDFile(self.configuration["xtd_file"]["filename"])
        
        self._xtdfile.build_universe()
        
        self._universe = self._xtdfile.universe
        
        self._trjfile = TrjFile(self.configuration["trj_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._trjfile['n_frames']
        
        self._velocities = None
        self._gradients = None

        data_to_be_written = ["configuration","time"]              
        if self._trjfile["velocities_written"]:
            self._universe.initializeVelocitiesToTemperature(0.)
            self._velocities = ParticleVector(self._universe)
            self._velocities.array[:,:] = 0.0
            data_to_be_written.append("velocities")

        if self._trjfile["gradients_written"]:
            self._universe.initializeVelocitiesToTemperature(0.)
            self._gradients = ParticleVector(self._universe)
            self._gradients.array[:,:] = 0.0
            data_to_be_written.append("gradients")

        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_files']['files'][0], mode='w', comment=self._trjfile["title"])

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, data_to_be_written, 0, None, 1)])
                
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
                                                
        # The x, y and z values of the current frame.
        time, cell, xyz, velocities, gradients = self._trjfile.read_step(index)
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        if self._universe.is_periodic and self._trjfile["defcel"]:
            self._universe.setShape(cell)
            
        movableAtoms = self._trjfile['mvofst']
                    
        self._universe.configuration().array[movableAtoms,:] = xyz
                   
        self._universe.foldCoordinatesIntoBox()
        
        data = {"time" : time}

        if self._velocities is not None:
            self._velocities.array[movableAtoms,:] = velocities
            data["velocities"] = self._velocities

        if self._gradients is not None:
            self._gradients.array[movableAtoms,:] = gradients
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
        
        self._trjfile.close()

        # Close the output trajectory.
        self._trajectory.close()

REGISTRY['forcite'] = ForciteConverter
