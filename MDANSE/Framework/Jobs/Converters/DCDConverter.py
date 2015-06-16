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
import struct

import numpy

from MMTK import Units
from MMTK.ParticleProperties import Configuration
from MMTK.PDB import PDBConfiguration
from MMTK.Trajectory import Trajectory, SnapshotGenerator, TrajectoryOutput
from MMTK.Universe import InfiniteUniverse, ParallelepipedicPeriodicUniverse

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.Converters.Converter import Converter
from MDANSE.Mathematics.Geometry import get_basis_vectors_from_cell_parameters
from MDANSE.MolecularDynamics.Trajectory import resolve_undefined_molecules_name

PI_2 = 0.5*numpy.pi
RECSCALE32BIT = 1
RECSCALE64BIT = 2

class DCDFileError(Error):
    pass
  
class ByteOrderError(Error):
    pass

class InputOutputError(Error):
    pass

class EndOfFile(Error):
    pass

class FortranBinaryFileError(Error):
    pass

def get_byte_order(filename):

    # Identity the byte order of the file by trial-and-error
    byteOrder = None

    # The DCD file is opened for reading in binary mode.
    data = file(filename, 'rb').read(4)

    # Check for low and big endianness byte orders.
    for order in ['<', '>']:
        reclen = struct.unpack(order + 'i', data)[0]
        if reclen == 84:
            byteOrder = order
            break

        if byteOrder is None:
            raise ByteOrderError("Invalid byte order. %s is not a valid DCD file" % filename)
                
    return byteOrder

class FortranBinaryFile(object):
    """Sets up a Fortran binary file reader. 

    @note: written by Konrad Hinsen.
    """
    def __init__(self, filename):
        """The constructor.

        @param filename: the input file.
        @type filename: string.

        @param byte_order: the byte order to read the binary file.
        @type byte_order: string being one '@', '=', '<', '>' or '!'.
        """
        self.file = file(filename, 'rb')
        self.byteOrder = get_byte_order(filename)

    def __iter__(self):
        return self

    def next_record(self):
        data = self.file.read(struct.calcsize("i"))
        if not data:
            raise StopIteration
        reclen = struct.unpack(self.byteOrder + 'i', data)[0]
        data = self.file.read(reclen)
        reclen2 = struct.unpack(self.byteOrder + 'i', self.file.read(struct.calcsize("i")))[0]
        if reclen != reclen2:
            FortranBinaryFileError("Invalid block")
            
        return data

    def skip_record(self):
        data = self.file.read(struct.calcsize("i"))
        reclen = struct.unpack(self.byteOrder + 'i', data)[0]
        self.file.seek(reclen, 1)
        reclen2 = struct.unpack(self.byteOrder + 'i', self.file.read(4))[0]
        assert reclen==reclen2

    def get_record(self, fmt, repeat = False):
        """Reads a record of the binary file.

        @param format: the format corresponding to the binray structure to read.
        @type format: string.        

        @param repeat: if True, will repeat the reading.
        @type repeat: bool.        
        """

        try:
            data = self.next_record()
        except StopIteration:
            raise EndOfFile()
        if repeat:
            unit = struct.calcsize(self.byteOrder + fmt)
            assert len(data) % unit == 0
            fmt = (len(data)/unit) * fmt
        try:
            return struct.unpack(self.byteOrder + fmt, data)
        except:
            raise                
  
class DCDFile(FortranBinaryFile, dict):
        
    def __init__(self, filename):
        
        FortranBinaryFile.__init__(self, filename)
                        
        self['filename'] = filename
                                        
        self.read_header()
        
    def read_header(self):
        
        # Read a block
        data = self.next_record()
                
        if data[:4] != 'CORD':
            raise DCDFileError("Unrecognized DCD format")

        temp = struct.unpack(self.byteOrder + '20i', data[4:])
        
        self['charmm'] = temp[-1]
                
        if self['charmm']:
            temp = struct.unpack(self.byteOrder + '9if10i', data[4:])
        else:
            temp = struct.unpack(self.byteOrder + '9id9i', data[4:])

        # Store the number of sets of coordinates
        self['nset'] = self['n_frames'] = temp[0]
        
        # Store the starting time step
        self['istart'] = temp[1]
        
        # Store the number of timesteps between dcd saves
        self['nsavc'] = temp[2]
        
        # Stores the number of fixed atoms
        self['namnf'] = temp[8]

        # Stop if there are fixed atoms.
        if self['namnf'] > 0:
            raise DCDFileError('Can not handle fixed atoms yet.')
                                        
        self['delta'] = temp[9]
                                            
        self["time_step"] = self['nsavc']*self['delta']*Units.akma_time           

        self['has_pbc_data'] = temp[10]

        self['has_4d'] = temp[11]
        
        # Read a block
        data = self.next_record()
                
        nLines = struct.unpack(self.byteOrder + b'I', data[0:4])[0]
            
        self["title"] = []
        for i in range(nLines):                
            temp = struct.unpack(self.byteOrder + '80c', data[4+80*i:4+80*(i+1)])
            self["title"].append("".join(temp).strip())
        
        self["title"] = "\n".join(self["title"])
        
        # Read a block
        data = self.next_record()
        
        # Read the number of atoms.
        self['natoms'] = struct.unpack(self.byteOrder + b'I', data)[0]
                                                            
    def read_step(self):
        """
        Reads a frame of the DCD file.
        """
                
        if self['has_pbc_data']:
            unitCell = numpy.array(self.get_record('6d'), dtype = numpy.float64)
            unitCell = unitCell[[0,2,5,1,3,4]]
            unitCell[0:3] *= Units.Ang
            # This file was generated by CHARMM, or by NAMD > 2.5, with the angle
            # cosines of the periodic cell angles written to the DCD file.       
            # This formulation improves rounding behavior for orthogonal cells   
            # so that the angles end up at precisely 90 degrees, unlike acos().            
            if numpy.all(abs(unitCell[3:]) <= 1):
                unitCell[3:] = PI_2 - numpy.arcsin(unitCell[3:])
            else:
                # assume the angles are stored in degrees (NAMD <= 2.5)
                unitCell[3:] *= Units.deg
            

        else:
            unitCell = None

        fmt = '%df' % self['natoms']
        config = numpy.empty((self["natoms"],3),dtype=numpy.float64)
        config[:,0] = numpy.array(self.get_record(fmt), dtype=numpy.float64)
        config[:,1] = numpy.array(self.get_record(fmt), dtype=numpy.float64)
        config[:,2] = numpy.array(self.get_record(fmt), dtype=numpy.float64)
        config *= Units.Ang
        
        if self['has_4d']:
            self.skip_record()
            
        return unitCell, config

    def skip_step(self):
        """Skips a frame of the DCD file.
        """
        nrecords = 3
        if self['has_pbc_data']:
            nrecords += 1
        if self['has_4d']:
            nrecords += 1
        for _ in range(nrecords):
            self['binary'].skip_record()

    def __iter__(self):
        return self

    def next_step(self):
        try:
            return self.read_step()
        except EndOfFile:
            raise StopIteration

class DCDConverter(Converter):
    """
    Converts a DCD trajectory to a MMTK trajectory.
    """
    
    type = None

    settings = collections.OrderedDict()
    settings['pdb_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','CHARMM','2vb1.pdb')})
    settings['dcd_file'] = ('input_file',{'default':os.path.join('..','..','..','Data','Trajectories','CHARMM','2vb1.dcd')})
    settings['output_file'] = ('output_files', {'formats':["netcdf"]})
    settings['fold'] = ('boolean', {'default':False,'label':"Fold coordinates in to box"})    

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.configuration["dcd_file"]["instance"] = DCDFile(self.configuration["dcd_file"]['filename'])

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration['dcd_file']['instance']['n_frames']
 
        # Create all objects from the PDB file.  
        conf = PDBConfiguration(self.configuration['pdb_file']['filename'])

        # Creates a collection of all the chemical objects stored in the PDB file
        molecules = conf.createAll()
                        
        # If the input trajectory has PBC create a periodic universe.
        if self.configuration['dcd_file']['instance']['has_pbc_data']:
            self._universe = ParallelepipedicPeriodicUniverse()
            
        # Otherwise create an infinite universe.
        else:
            self._universe = InfiniteUniverse()
                    
        # The chemical objects found in the PDB file introduced into the universe.
        self._universe.addObject(molecules)

        resolve_undefined_molecules_name(self._universe)
        
        # A MMTK trajectory is opened for writing.
        self._trajectory = Trajectory(self._universe, self.configuration['output_file']['files'][0], mode='w')
        
        # A frame generator is created.        
        self._snapshot = SnapshotGenerator(self._universe, actions=[TrajectoryOutput(self._trajectory, ["all"], 0, None, 1)])

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
        """
                        
        # The x, y and z values of the current frame.
        unitCell, config = self.configuration["dcd_file"]["instance"].read_step()
        
        conf = Configuration(self._universe,config)
        
        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        if self._universe.is_periodic:
            self._universe.setShape(get_basis_vectors_from_cell_parameters(unitCell))
        
        self._universe.setConfiguration(conf)
        
        if self.configuration['fold']["value"]:        
            self._universe.foldCoordinatesIntoBox()
                                                   
        # The current time.
        t = (index+1)*self.configuration["dcd_file"]["instance"]['time_step']

        # Store a snapshot of the current configuration in the output trajectory.
        self._snapshot(data={'time': t})
                                        
        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """   
        
        pass
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 

        # Close the output trajectory.
        self._trajectory.close()