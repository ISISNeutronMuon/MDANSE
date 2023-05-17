# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/VASP.py
# @brief     Implements module/class/test VASP
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

import numpy

from MMTK import Atom
from MMTK import Units
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converter import Converter


class XDATCARFileError(Error):
    pass


class VASPConverterError(Error):
    pass


class XDATCARFile(dict):
    
    def __init__(self, filename):
        
        self['instance'] = open(filename, 'rb')

        # Read header
        self["instance"].readline()
        header = []
        while True:
            self._headerSize = self["instance"].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith("direct"):
                self._frameHeaderSize = self["instance"].tell() - self._headerSize
                break
            header.append(line)
                                   
        self["scale_factor"] = float(header[0])

        cell = " ".join(header[1:4]).split()

        cell = numpy.array(cell,dtype=numpy.float64)
                
        self["cell_shape"] = numpy.reshape(cell,(3,3))*Units.Ang*self["scale_factor"]
                    
        self["atoms"] = list(zip(header[4].split(),[int(v) for v in header[5].split()]))
                    
        self["n_atoms"] = sum([v[1] for v in self["atoms"]])
        
        # The point here is to determine if the trajectory is NVT or NPT. If traj is NPT, the box will change at each iteration and the "header" will appear betwwen every frame
        # We try to read the two first frames to figure it out
        nAtoms = 0
        while True:
            self._frameSize = self['instance'].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith("direct"):
                break
            nAtoms += 1
                    
        if nAtoms == self["n_atoms"]:
            # Traj is NVT
            # Structure is
            # Header
            # FrameHeader
            # Frame 1
            # FrameHeader
            # Frame 2
            # ...
            # With frameHeader being "dummy"
            self._npt = False
            self._frameSize -= self._headerSize
            self._actualFrameSize = self._frameSize - self._frameHeaderSize
        else:
            # Traj is NPT
            # Structure is
            # FrameHeader
            # Frame 1
            # FrameHeader
            # Frame 2
            # ...
            # With FrameHeader containing box size
            self._npt = True
            self._actualFrameSize = self._frameSize
            self._frameSize -= self._headerSize
            self._frameHeaderSize += self._headerSize
            self._headerSize = 0
            self._actualFrameSize = self._frameSize - self._frameHeaderSize
            # Retry to read the first frame
            self["instance"].seek(self._frameHeaderSize)
            nAtoms = 0
            while True:
                self._frameSize = self['instance'].tell()
                line = self["instance"].readline().strip()
                if len(line.split("  ")) != 3:
                    break
                nAtoms += 1

            if nAtoms != self["n_atoms"]:
                # Something went wrong
                raise XDATCARFileError("The number of atoms (%d) does not match the size of a frame (%d)." % (nAtoms, self["n_atoms"]))
            
        # Read frame number
        self["instance"].seek(0,2)
        self["n_frames"] = (self['instance'].tell()-self._headerSize)/self._frameSize
        
        # Go back to top
        self["instance"].seek(0)
                
                
    def read_step(self, step):
        self['instance'].seek(self._headerSize+step*self._frameSize)
        
        if self._npt:
            # Read box size
            self["instance"].readline()
            header = []
            while True:
                line = self["instance"].readline().strip()
                if not line or line.lower().startswith("direct"):
                    break
                header.append(line)
            cell = " ".join(header[1:4]).split()
            cell = numpy.array(cell,dtype=numpy.float64)
            self["cell_shape"] = numpy.reshape(cell,(3,3))*Units.Ang*self["scale_factor"]
        else:
            self['instance'].read(self._frameHeaderSize)
                        
        data = numpy.array(self['instance'].read(self._actualFrameSize).split(), dtype=numpy.float64)
        
        config = numpy.reshape(data,(self["n_atoms"],3))
                                                        
        return config
                                
    def close(self):
        self["instance"].close()


class VASPConverter(Converter):
    """
    Converts a VASP trajectory to a MMTK trajectory.
    """
                  
    label = "VASP (>=5)"

    settings = collections.OrderedDict()           
    settings['xdatcar_file'] = ('input_file',{'wildcard':'XDATCAR files (XDATCAR*)|XDATCAR*|All files|*',
                                                'default':os.path.join('..','..','..','Data','Trajectories','VASP','XDATCAR_version5')})
    settings['time_step'] = ('float', {'label':"time step", 'default':1.0, 'mini':1.0e-9})        
    settings['output_file'] = ('single_output_file', {'format':"netcdf",'root':'xdatcar_file'})
                
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        self._xdatcarFile = XDATCARFile(self.configuration["xdatcar_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._xdatcarFile['n_frames']
        
        self._universe = ParallelepipedicPeriodicUniverse()
        
        for symbol,number in self._xdatcarFile["atoms"]:
            for i in range(number):
                self._universe.addObject(Atom(symbol, name="%s_%d" % (symbol,i)))        

        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['file'], mode='w')

        data_to_be_written = ["configuration","time"]

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, data_to_be_written, 0, None, 1)])

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        # Read the current step in the xdatcar file.
        config = self._xdatcarFile.read_step(index)
        
        self._universe.setShape(self._xdatcarFile["cell_shape"])
        
        conf = Configuration(self._universe,config)
        
        conf.convertFromBoxCoordinates()
        
        self._universe.setConfiguration(conf)
                                        
        # The real coordinates are foled then into the simulation box (-L/2,L/2). 
        self._universe.foldCoordinatesIntoBox()

        time = index*self.configuration["time_step"]["value"]*Units.fs

        # A call to the snapshot generator produces the step corresponding to the current frame.
        self._snapshot(data = {'time': time})

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
        
        self._xdatcarFile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(VASPConverter,self).finalize()


REGISTRY['vasp'] = VASPConverter

