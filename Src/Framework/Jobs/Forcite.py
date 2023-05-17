# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Forcite.py
# @brief     Implements module/class/test Forcite
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import struct

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.Units import measure
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.Framework.Jobs.MaterialsStudio import XTDFile
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

FORCE_FACTOR = measure(1.0,"kcal_per_mole/ang",equivalent=True).toval("uma nm/ps2 mol")

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
        self["title"] = "\n".join([t.decode('utf-8') for t in self["title"]])
        
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
        self["mvofst"] = np.array(struct.unpack(rec,trjfile.read(recSize)), dtype=np.int32) - 1

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
        
        self["n_frames"] = (trjfile.tell()-self._headerSize)//self._frameSize
        
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
            cell = np.zeros((3,3),dtype=np.float64)
            # ax,by,cz,bz,az,ay            
            cellData = np.array(struct.unpack(self._defCellRec,trjfile.read(self._defCellRecSize)),dtype=np.float64)[2:8]*measure(1.0,'ang').toval('nm')
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
                config = np.transpose(np.reshape(config,(3,3, self['totmov'])))
                xyz    = config[:,:,0]*measure(1.0,'ang').toval('nm')
                vel    = config[:,:,1]*measure(1.0,'ang/fs').toval('nm/ps')
                gradients = config[:,:,2]*FORCE_FACTOR
            else:
                config = np.transpose(np.reshape(config,(2,3, self['totmov'])))
                xyz    = config[:,:,0]*measure(1.0,'ang').toval('nm')
                vel    = config[:,:,1]*measure(1.0,'ang/fs').toval('nm/ps')
                gradients = None
        else:
            if self["gradients_written"]:
                config = np.transpose(np.reshape(config,(2,3, self['totmov'])))
                xyz    = config[:,:,0]*measure(1.0,'ang').toval('nm')
                vel    = None
                gradients = config[:,:,1]*FORCE_FACTOR
            else:
                config = np.transpose(np.reshape(config,(1,3, self['totmov'])))
                xyz    = config[:,:,0]*measure(1.0,'ang').toval('nm')
                vel    = None
                gradients = None
            
        return timeStep, cell, xyz, vel, gradients

    def close(self):
        self["instance"].close()
        
class ForciteConverter(Converter):
    """
    Converts a Forcite trajectory to a HDF trajectory.
    """
    
    label = "Forcite"

    category = ('Converters','Materials Studio')
    
    settings = collections.OrderedDict()
    settings['xtd_file'] = ('input_file', {'wildcard':'XTD files (*.xtd)|*.xtd|All files|*',
                                           'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'Forcite',
                                                                   'H2O.xtd')})
    settings['trj_file'] = ('input_file', {'wildcard': 'TRJ files (*.trj)|*.trj|All files|*',
                                           'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'Forcite',
                                                                   'H2O.trj')})
    settings['fold'] = ('boolean', {'default':False,'label':"Fold coordinates in to box"})    
    settings['output_file'] = ('single_output_file', {'format': 'hdf', 'root': 'xtd_file'})

    def initialize(self):
        '''
        Initialize the job.
        '''
        
        self._xtdfile = XTDFile(self.configuration["xtd_file"]["filename"])
        
        self._xtdfile.build_chemical_system()
        
        self._chemicalSystem = self._xtdfile.chemicalSystem
        
        self._trjfile = TrjFile(self.configuration["trj_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._trjfile['n_frames']
        
        if self._trjfile["velocities_written"]:
            self._velocities = np.zeros((self._chemicalSystem.number_of_atoms(),3),dtype=np.float)
        else:
            self._velocities = None

        if self._trjfile["gradients_written"]:
            self._gradients = np.zeros((self._chemicalSystem.number_of_atoms(),3),dtype=np.float)
        else:
            self._gradients = None

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration['output_file']['file'], 
            self._chemicalSystem,
            self.numberOfSteps)
                
    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """
                                                
        # The x, y and z values of the current frame.
        time, cell, xyz, velocities, gradients = self._trjfile.read_step(index)
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        conf = self._trajectory.chemical_system.configuration
        movableAtoms = self._trjfile['mvofst']
        conf['coordinates'][movableAtoms,:] = xyz
        if conf.is_periodic:
            if self._trjfile["defcel"]:
                conf.unit_cell = cell
            if self._configuration['fold']['value']:
                conf.fold_coordinates()
                           
        if self._velocities is not None:
            self._velocities[movableAtoms,:] = velocities
            conf["velocities"] = self._velocities

        if self._gradients is not None:
            self._gradients[movableAtoms,:] = gradients
            conf["gradients"] = self._gradients

        self._trajectory.dump_configuration(time,units={'time':'ps','unit_cell':'nm','coordinates':'nm','velocities':'nm/ps','gradients':'uma nm/ps2'})

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

        super(ForciteConverter,self).finalize()

REGISTRY['forcite'] = ForciteConverter
