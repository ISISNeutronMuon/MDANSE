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

import numpy

from MMTK import Atom
from MMTK import Units
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import ParallelepipedicPeriodicUniverse

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converters.Converter import Converter

class XDATCARFileError(Error):
    pass

class VASPConverterError(Error):
    pass

class XDATCARFile(dict):
    
    def __init__(self, filename):
        
        self['instance'] = open(filename, 'rb')

        self["instance"].readline()
        header = []
        while True:
            self._headerSize = self["instance"].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith("direct"):
                self._dummyLineSize = self["instance"].tell() - self._headerSize
                break
            header.append(line)
                                                        
        self["scale_factor"] = float(header[0])

        cell = " ".join(header[1:4]).split()

        cell = numpy.array(cell,dtype=numpy.float64)
                
        self["cell_shape"] = numpy.reshape(cell,(3,3))*Units.Ang*self["scale_factor"]
                    
        self["atoms"] = zip(header[4].split(),[int(v) for v in header[5].split()])
                    
        nAtoms = sum([v[1] for v in self["atoms"]])
                                    
        self["n_atoms"] = 0
        while True:
            self._frameSize = self['instance'].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith("direct"):
                break
            self["n_atoms"] += 1
            
        if nAtoms != self["n_atoms"]:
            raise XDATCARFileError("The number of atoms (%d) does not match the size of a frame (%d)." % (nAtoms,["n_atoms"]))
            
        self._frameSize -= self._headerSize
        
        self._actualFrameSize = self._frameSize - self._dummyLineSize

        self["instance"].seek(0,2)
        
        self["n_frames"] = (self['instance'].tell()-self._headerSize)/self._frameSize

        self["instance"].seek(0)
                
                
    def read_step(self, step):
        
        self['instance'].seek(self._headerSize+step*self._frameSize)
        self['instance'].read(self._dummyLineSize)
                        
        data = numpy.array(self['instance'].read(self._actualFrameSize).split(), dtype=numpy.float64)
        
        config = numpy.reshape(data,(self["n_atoms"],3))
                                                        
        return config
    
                                
    def close(self):
        self["instance"].close()

class VASPConverter(Converter):
    """
    Converts a VASP trajectory to a MMTK trajectory.
    """
              
    type = 'vasp'
    
    label = "VASP (>=5)"

    category = ('Converters',)
    
    ancestor = []

    settings = collections.OrderedDict()           
    settings['xdatcar_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','VASP','XDATCAR_version5')})
    settings['time_step'] = ('float', {'label':"time step", 'default':1.0, 'mini':1.0e-9})        
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        '''
        Initialize the job.
        '''
                
        self._xdatcarFile = XDATCARFile(self.configuration["xdatcar_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._xdatcarFile['n_frames']
        
        self._universe = ParallelepipedicPeriodicUniverse()
        self._universe.setShape(self._xdatcarFile["cell_shape"])
        
        for symbol,number in self._xdatcarFile["atoms"]:
            for i in range(number):
                self._universe.addObject(Atom(symbol, name="%s_%d" % (symbol,i)))        

        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], mode='w')

        # A frame generator is created.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])

    def run_step(self, index):
        """Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.      
        """

        # Read the current step in the xdatcar file.
        config = self._xdatcarFile.read_step(index)
        
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